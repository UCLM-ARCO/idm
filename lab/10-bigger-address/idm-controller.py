#!/usr/bin/python3
# -*- mode: python; coding: utf-8 -*-

import logging
import os
import sys
import argparse
import json
import pickle
import hashlib
from threading import Thread, Event
from functools import wraps
from flask import Flask, render_template, Response, request
import Ice

Ice.loadSlice("/usr/share/slice/idm/idm.ice")
import IDM


def padstr(s, padding=4):
    return str(s).replace("\n", "\n" + padding * " " + "> ")


def async_call(fn, *args, **kwargs):
    t = Thread(target=fn, args=args, kwargs=kwargs)
    t.daemon = True
    t.start()


class FlowNode:
    def __init__(self, next_hop, *, ui_options=None):
        self.next_hop = next_hop
        self.ui_options = ui_options or {}


class RouterNode:
    def __init__(self, address, proxy, *, managed=False, ui_options=None):
        self.address = address
        self.proxy = proxy
        self.managed = managed
        self.ui_options = ui_options or {}
        self.flows = {}


class Network:
    def __init__(self, ic, *, store_path="saved_state.bin"):
        self.ic = ic
        self.store_path = store_path
        self.nodes = {}
        self.on_change = Event()

        if os.path.exists(store_path):
            self.load_state()

    def __del__(self):
        self.save_state()

    def save_state(self):
        with open(self.store_path, "wb") as dst:
            pickle.dump(self.nodes, dst)

    def load_state(self):
        try:
            with open(self.store_path, "rb") as src:
                self.nodes = pickle.load(src)
        except Exception as e:
            logging.warning(" could not restore saved state, " + str(e))

    def add_router(self, proxy, *, managed=False):
        address = proxy.split(" ")[0]
        node = RouterNode(address, proxy, managed=managed)

        if address in self.nodes:
            if self.update_existing_router(node):
                self.notify_on_change()
        else:
            self.add_new_router(node)
            self.notify_on_change()

        self.save_state()

    def update_existing_router(self, node):
        logging.info(" already added router: {}".format(node.address))

        current = self.nodes[node.address]
        if current.proxy and not self.proxy_equals(current.proxy, node.proxy):
            msg = " - there are two or more endpoints for router {}:\n".format(node.address)
            msg += node.proxy + "\n" + current.proxy
            msg += "\nusing most recent one!"
            logging.warn(padstr(msg))

            # treat old router as a not managed
            current.managed = False

        # if node wasn't managed and now it is, load its flows
        current.proxy = node.proxy
        if not current.managed and node.managed:
            self.load_router_flows(current)

        current.managed = current.managed or node.managed
        return True

    def add_new_router(self, node):
        logging.info(" adding new router: {}, managed: {}".format(node.address, node.managed))
        self.nodes[node.address] = node

        # only if router is managed, load its flows
        if node.managed:
            self.load_router_flows(node)

    def load_router_flows(self, node):
        logging.info(" - loading flows of {}".format(node.address))

        # create proxy and cast to RouterAdmin
        router = self.get_router(node.proxy, node.address)
        if router is None:
            return

        flows = router.flowList()
        for f in flows:
            # if destination and routeID are equal, direct delivery
            router_id = f.a.next.split(" ")[0]
            if f.m.address == router_id:
                continue

            # otherwise, 'next' is a router, add it if not present
            if router_id not in self.nodes:
                self.add_router(f.a.next, managed=False)

            # update router node
            node.flows[f.m.address] = FlowNode(router_id)

    def get_router(self, proxy, address="<unknown>"):
        try:
            router = self.ic.stringToProxy(proxy)
            router = IDM.Routing.RouterAdminPrx.checkedCast(router)
            if router is None:
                raise TypeError("checked cast return None")
        except (Ice.Exception, TypeError) as ex:
            logging.warning(" - could not contact with {}: {}".format(address, padstr(ex)))
            router = None
        return router

    def proxy_equals(self, a, b):
        try:
            a = self.ic.stringToProxy(a)
            b = self.ic.stringToProxy(b)
            return a == b
        except Ice.Exception:
            return False

    def notify_on_change(self):
        self.on_change.set()
        self.on_change.clear()

    def notify_on_close(self):
        self.on_change.set()

    def wait_for_changes(self):
        self.on_change.wait()

    def to_json(self):
        return json.dumps(self.nodes, default=lambda o: o.__dict__)

    def merge(self, other):
        routers = []
        links = []

        for c in other['cells']:
            if c['type'] == "idm.RouterShape":
                routers.append(c)
            elif c['type'] == "devs.Link":
                links.append(c)
            else:
                logging.warning(" unknown cell type: {}".format(c['type']))
                continue

        nodes = self.merge_routers(routers)
        self.merge_links(links, nodes)
        self.save_state()

    def merge_routers(self, routers):
        nodes_by_id = {}
        for r in routers:
            try:
                rid = r['id']
                attrs = r['attrs']
                position = r['position']
                pos_x = position['x']
                pos_y = position['y']
                address = attrs['address']['text']
            except KeyError as e:
                logging.warning(" invalid formatted node (missing {}), ignoring".format(str(e)))
                continue

            ui_options = {'position': (pos_x, pos_y)}
            node = self.nodes.get(address)
            if node is None:
                node = RouterNode(address, None, managed=False)
                self.add_new_router(node)

            node.ui_options = ui_options
            node.flows = {}
            nodes_by_id[rid] = node

        return nodes_by_id

    def merge_links(self, links, nodes):
        for l in links:
            try:
                lid = l['id']
                source = l['source']
                source_id = source['id']
                source_selector = source['selector']
                target = l['target']
                target_id = target['id']
                target_selector = target['selector']
                attrs = l['attrs']
                matcher = l['matcher']['address']
            except KeyError as e:
                logging.warning(" invalid formatted node (missing {}), ignoring".format(str(e)))
                continue

            ui_options = {
                'source_selector': source_selector,
                'target_selector': target_selector,
                'vertices': [] if "vertices" not in l else l['vertices'],
            }

            source_node = nodes.get(source_id)
            target_node = nodes.get(target_id)
            source_node.flows[matcher] = FlowNode(target_node.address, ui_options=ui_options)

    def deploy_flows(self):
        for r in self.nodes.values():
            router = self.get_router(r.proxy, r.address)
            if router is None:
                continue

            # for each router, remove current routed flows
            flows = router.flowList()
            for f in flows:
                # if destintation is other router, remove flow
                router_id = f.a.next.split(" ")[0]
                if f.m.address == router_id:
                    continue
                router.flowDelete(f.identifier)

            # for each link on graph, add a new flow
            for dst, node in r.flows.items():
                next_hop = self.nodes[node.next_hop].proxy
                matcher = IDM.Routing.Matcher(dst)
                action = IDM.Routing.Action(IDM.Routing.ActionType.Forward, next_hop)
                flow = IDM.Routing.Flow(0, matcher, action)
                router.flowAdd(flow)


class ControllerI(IDM.Controller):
    def __init__(self, network):
        self.network = network

    def newNeighbor(self, proxy, routerAddr, current):
        logging.info(" new neighbor: {} -> {}".format(routerAddr, str(proxy)))

    def newRouter(self, proxy, current):
        logging.info(" new router: {}".format(str(proxy)))
        async_call(self.network.add_router, proxy, managed=True)

    def matchingError(self, message, current):
        logging.info(" matching error: dst: {}, op: {}, params: {}, ctx: {}".format(
            message.destination, message.operation, message.inParams, message.theContext
        ))


class ControllerService:
    def __init__(self, args):
        self.args = args

        self.ic = Ice.initialize(sys.argv)
        self.adapter = self.ic.createObjectAdapter("Adapter")
        self.adapter.activate()

        store_path = self.ic.getProperties().getPropertyWithDefault(
            "IDM.Controller.Store.Path", "/tmp/idm-controller-saved-state.bin")
        self.network = Network(self.ic, store_path=store_path)

        oid = Ice.stringToIdentity("RouterController")
        proxy = self.adapter.add(ControllerI(self.network), oid)
        logging.info(" controller ready: '{}'".format(str(proxy)))

    def __del__(self):
        if hasattr(self, "ic") and self.ic:
            self.ic.destroy()

    def loop(self):
        logging.info(" waiting events...")
        try:
            self.ic.waitForShutdown()
        except KeyboardInterrupt:
            print("\rBye!")


class WebServer:
    def __init__(self, args, network):
        self.args = args
        self.network = network
        self.should_stop = False

        # search for a valid assets folder
        pwd = os.path.abspath(os.path.dirname(__file__))
        self.assets = os.path.join(pwd, "webui")
        if not os.path.exists(self.assets):
            self.assets = "/usr/share/idm-controller/webui"

        templates = os.path.join(self.assets, "templates")
        static = os.path.join(self.assets, "static")
        self.app = Flask(__name__, static_folder=static, template_folder=templates)
        self.setup_handlers()

    def loop(self):
        if self.args.disable_flask_log:
            url = "http://{}:{}/".format(self.args.host, self.args.port)
            logging.info(" WebUI ready, visit '{}'".format(url))

        logging.info(" waiting events...")
        self.app.run(threaded=True, host=self.args.host, port=self.args.port)
        self.should_stop = True
        self.network.notify_on_close()

    def setup_handlers(self):
        def check_auth(given_username, given_password):
            try:
                given_password = given_password.encode("utf-8")
                given_password = hashlib.sha256(given_password).hexdigest()
                with open(self.args.credentials) as src:
                    line = src.readline().strip()
                    real_user, real_passwd = line.split(":")
                    return given_username == real_user and given_password == real_passwd
            except Exception as e:
                logging.error(" error while checking auth: " + str(e))
                return False

        def authenticate():
            return Response(
                'Sorry, that didn\'t work. Please, login again.', 401,
                {'WWW-Authenticate': 'Basic realm="Login Required"'}
            )

        def requires_auth(f):
            @wraps(f)
            def decorated(*args, **kwargs):
                auth = request.authorization
                if not auth or not check_auth(auth.username, auth.password):
                    return authenticate()
                return f(*args, **kwargs)
            return decorated

        @self.app.route("/")
        @requires_auth
        def index():
            return render_template("index.html")

        @self.app.route("/network")
        @requires_auth
        def get_network():
            return Response(self.network.to_json(), mimetype="application/json")

        @self.app.route("/deploy", methods=["POST"])
        @requires_auth
        def do_deploy():
            logging.info(" deploy called")
            net = request.get_json()
            self.network.merge(net)
            async_call(self.network.deploy_flows)
            return Response("OK")

        @self.app.route("/updates")
        @requires_auth
        def send_updates():
            def wait_for_changes():
                while True:
                    if self.should_stop:
                        return
                    self.network.wait_for_changes()
                    data = self.network.to_json()
                    yield "data: {}\n\n".format(data)

            return Response(wait_for_changes(), mimetype="text/event-stream")


class Server:
    def __init__(self, args):
        self.args = args
        self.controller = ControllerService(args)
        if not self.args.no_web_ui:
            self.webserver = WebServer(args, self.controller.network)

    def run(self):
        if self.args.no_web_ui:
            self.controller.loop()
        else:
            self.webserver.loop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--no-web-ui", action="store_true",
                        help="do no launch the web interface")
    parser.add_argument("--host", default="0.0.0.0",
                        help="host address where web server will listen")
    parser.add_argument("--port", type=int, default=8000,
                        help="port number where web server will listen")
    parser.add_argument("--disable-flask-log", action="store_true",
                        help="disable logging of web server")
    parser.add_argument("--credentials", default="users.cred",
                        help="file where user credentials are stored")

    _args = parser.parse_known_args()[0]

    # set Flask logging to ERROR
    if _args.disable_flask_log:
        werkzeug = logging.getLogger('werkzeug')
        werkzeug.setLevel(logging.ERROR)

    Server(_args).run()
