#!/usr/bin/python3 -u
# -*- mode: python; coding: utf-8 -*-

import os
import sys
import time
import Ice
import IceStorm
from queue import Queue, Full
from argparse import ArgumentParser
from threading import RLock, Thread
from collections import OrderedDict

import logging
logging.getLogger().setLevel(logging.INFO)


def load_slice(name, parent=""):
    pwd = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(pwd, name)
    if not os.path.exists(path):
        path = "/usr/share/slice/{}{}".format(parent, name)

    Ice.loadSlice("{} -I{} -I{} -I/usr/share/slice --all".format(path, pwd, Ice.getSliceDir()))

load_slice("idm.ice", "idm/")
load_slice("duo_idm.ice", "duo/")
import IDM
import DUO


MAX_ADDRESS_SIZE = 16  # given in bytes


def expand_address(addr, netmask=MAX_ADDRESS_SIZE):
    addr = int(netmask - len(addr) / 2) * "00" + addr
    if len(addr) > MAX_ADDRESS_SIZE * 2:
        raise ValueError("Invalid address: {}/{}".format(addr, netmask))
    net = addr[:netmask * 2]
    host = addr[netmask * 2:]
    return net + int(MAX_ADDRESS_SIZE * 2 - len(addr)) * "0" + host


def get_property(ic, name):
    props = ic.getProperties()
    value = props.getProperty(name)
    if value == "":
        raise ValueError("Undefined property: '{}'".format(name))
    return value


class NoSuchRoute(Exception):
    pass


class FlowInfo:
    def __init__(self, destination, netmask, router_id, router_endps, mode, id=None):
        self.dst_oid = destination
        self.destination = expand_address(destination, netmask)
        self.netmask = netmask
        self.router_id = router_id
        self.router_endps = router_endps
        self.mode = mode
        self.id = id

    @classmethod
    def from_proxy(cls, proxy, destination=None, netmask=MAX_ADDRESS_SIZE):
        router_id, router_endps, mode = cls.get_proxy_info(proxy)
        if destination is None:
            destination = router_id
        return FlowInfo(destination, netmask, router_id, router_endps, mode)

    @classmethod
    def get_proxy_info(cls, proxy):
        router_id = Ice.identityToString(proxy.ice_getIdentity())
        router_id = router_id.replace(":", "").strip('" ').upper()
        router_endps = ":".join(map(str, proxy.ice_getEndpoints()))

        mode = "t"
        if proxy.ice_isDatagram():
            mode = "d"
        elif proxy.ice_isOneway():
            mode = "o"
        return router_id, router_endps, mode

    def __repr__(self):
        return "{} | {} | {} | {} | {}".format(
            self.dst_oid, self.netmask, self.router_id, self.router_endps, self.mode)


class RoutingTable(object):
    def __init__(self, ic, path, addresses):
        self.ic = ic
        self.path = path
        self.lock = RLock()

        # FIXME: use netmask size as sorting key
        self.routes = OrderedDict()

        self.router_address = []

        # parse router addresses with netmasks
        for addr in addresses:
            netmask = 15
            if "/" in addr:
                addr, netmask = addr.split("/")
                try:
                    netmask = int(netmask)
                    assert netmask >= 1 and netmask <= 16
                except (ValueError, AssertionError):
                    raise ValueError("Invalid netmask value, should be a number in range [1,16]")
            addr = expand_address(addr)
            self.router_address.append((addr, netmask))

        with open(path) as src:
            self.proccess_file(src)

    def add(self, flow_info):
        with self.lock:
            flow_info.id = self.get_id_for(flow_info.destination)
            self.routes[flow_info.destination] = flow_info
            self.store()

    def remove(self, destination):
        with self.lock:
            try:
                self.routes.pop(destination)
                self.store()
            except KeyError:
                pass

    def remove_by_id(self, id):
        with self.lock:
            dst = self.find_by_id(id)
            if dst is None:
                return None

            info = self.routes[dst]
            self.remove(dst)
            return info

    def find_by_id(self, id):
        with self.lock:
            for dst, info in list(self.routes.items()):
                if info.id == id:
                    return dst

    def get_id_for(self, destination):
        try:
            id = self.routes[destination].id
        except KeyError:
            id = 0
            for r in list(self.routes.values()):
                id = max(id, r.id)
            id += 1
        return id

    def list(self):
        return self.routes

    def proccess_file(self, src):
        for line in src:
            line = line.strip()
            if line.startswith(":"):
                continue

            try:
                destination, netmask, router_id, router_endps, mode = \
                    list(map(str.strip, line.split(" | ")))
                flow_info = FlowInfo(destination, netmask, router_id, router_endps, mode)
                self.add(flow_info)
            except Exception:
                logging.warn(" invalid line on routing table, ignoring...")

    def store(self):
        # FIXME: store in a separate thread, once each 5 mins (or so)
        header = ": DO NOT EDIT, it will be overwritten!\n"
        header += ": destination | routerId | endpoints | mode\n: " + "-" * 50 + "\n"
        with open(self.path, "w") as dst:
            dst.write(header)
            for destination in sorted(self.routes.keys()):
                info = self.routes[destination]
                dst.write(str(info) + "\n")

    def get_next(self, oid):
        oid = self.ic.identityToString(oid)
        dst = expand_address(oid)
        flow_info = self.routes.get(dst, None)

        # if not direct proxy, but is on our network: noSuchRoute
        if flow_info is None and self.is_local_address(dst):
            raise NoSuchRoute

        # try to get router for that specific network
        if flow_info is None:
            for addr, info in self.routes.items():
                bmask = info.netmask * 2
                if dst[:bmask] == addr[:bmask]:
                    flow_info = info
                    break

        # or try to get the default router
        if flow_info is None:
            flow_info = self.routes.get(MAX_ADDRESS_SIZE * "00", None)

        if flow_info is None:
            raise NoSuchRoute

        proxy = "{} -{}:{}".format(oid, flow_info.mode, flow_info.router_endps)
        proxy = self.ic.stringToProxy(proxy)
        proxy = proxy.ice_encodingVersion(Ice.Encoding_1_0)
        return proxy

    def is_local_address(self, dst):
        for addr, netmask in self.router_address:
            bmask = netmask * 2
            if dst[:bmask] == addr[:bmask]:
                return True
        return False


class IncommingMessage(object):
    def __init__(self, in_params, current):
        self.oid = current.id
        self.operation = current.operation
        self.mode = current.mode
        self.ctx = current.ctx.copy()
        self.in_params = bytes(in_params[:])


class Forwarder(Ice.Blobject):
    def __init__(self, table, controller, queue_size=10):
        self.table = table
        self.controller = controller
        self.queue = Queue(maxsize=int(queue_size))
        logging.info(" queue Size: {}".format(queue_size))

        # do forwarding on a separated thread
        t = Thread(target=self.forwarder_loop)
        t.daemon = True
        t.start()

    def __del__(self):
        self.table.store()

    def ice_invoke(self, in_params, current):
        msg = IncommingMessage(in_params, current)

        try:
            self.queue.put_nowait(msg)
        except Full:
            logging.error(" - could not forward message: full queue!")

        return True, bytes()

    def forwarder_loop(self):
        while True:
            msg = self.queue.get()
            self.process_message(msg)
            self.queue.task_done()

    def process_message(self, msg):
        try:
            next = self.table.get_next(msg.oid)
            logging.info(" - forward to '{}'".format(next))
            next.ice_invoke(msg.operation, msg.mode, msg.in_params, msg.ctx)

        except NoSuchRoute:
            oid = Ice.identityToString(msg.oid)
            logging.error(" - no route to '{}'".format(oid))
            if self.controller is not None:
                m = IDM.Message(Ice.identityToString(msg.oid),
                                msg.operation,
                                msg.in_params,
                                msg.ctx)

                def on_error(ex):
                    logging.error(" something went wrong when calling controller: " + ex.reason)

                self.controller.begin_matchingError(m, None, on_error)

        except Ice.Exception as e:
            logging.error(" - could not forward message: " + str(e))


class RouterI(IDM.Router):
    def __init__(self, table, controller, ic):
        self.table = table
        self.controller = controller
        self.ic = ic

    def flowAdd(self, flow, current):
        destination = flow.m.address
        netmask = flow.m.netmask

        try:
            next_prx = self.ic.stringToProxy(flow.a.next)
            flow_info = FlowInfo.from_proxy(next_prx, destination, netmask)
        except Ice.Exception as e:
            logging.error(" - could not add flow: " + str(e))
            return

        logging.info(" - flowAdd for '{}', dst: {}".format(destination, flow.a.next))
        self.table.add(flow_info)

    def flowDelete(self, id, current):
        flow_info = self.table.remove_by_id(id)
        rule = "not exists!"
        if flow_info is not None:
            rule = str(flow_info)
        logging.info(" - flowDelete of {}, rule {}".format(id, rule))

    def flowList(self, current):
        logging.info(" - flowList done")
        flows = []

        rows = self.table.list()
        for destination, info in list(rows.items()):
            matcher = IDM.Routing.Matcher(destination)
            nextHop = "{} -{}:{}".format(info.router_id, info.mode, info.router_endps)
            action = IDM.Routing.Action(IDM.Routing.ActionType.Forward, nextHop)
            flow = IDM.Routing.Flow(info.id, matcher, action)
            flows.append(flow)

        return flows

    def adv(self, proxy, current):
        try:
            flow_info = FlowInfo.from_proxy(self.ic.stringToProxy(proxy))
        except Ice.Exception as e:
            logging.error(" - invalid adv: " + str(e))
            return

        logging.info(" - adv from '{}'".format(proxy))
        self.table.add(flow_info)

        if self.controller is not None:
            address = Ice.identityToString(current.id)
            self.controller.newNeighbor(proxy, address)

    def bye(self, oid, current):
        logging.info(" - bye from '{}'".format(oid))
        self.table.remove(oid)


# A Wrapper, to maintain it decoupled
class DUOAdvertiser(IDM.Router):
    def __init__(self, instance):
        self.instance = instance
        self.ic = instance.ic
        self.enabled = False
        self.pub = self.get_publisher("announce")

        # redirect not-spied methods
        self.flowAdd = instance.flowAdd
        self.flowDelete = instance.flowDelete
        self.flowList = instance.flowList

    def get_publisher(self, topic_name):
        mgr = self.ic.propertyToProxy("IceStorm.TopicManager.Proxy")
        mgr = IceStorm.TopicManagerPrx.checkedCast(mgr)

        if mgr is None:
            logging.warn(" DUO advertisements disabled")
            return

        try:
            topic = mgr.retrieve(topic_name)
        except IceStorm.NoSuchTopic:
            topic = mgr.create(topic_name)

        pub = topic.getPublisher().ice_datagram()
        try:
            pub.ice_ping()
        except Ice.NoEndpointException:
            logging.warn(" DUO advertisements disabled")
            return

        self.enabled = True
        return DUO.IDM.ListenerPrx.uncheckedCast(pub)

    def get_idm_addr(self, str_proxy):
        proxy = self.ic.stringToProxy(str_proxy)
        oid = proxy.ice_getIdentity()
        return self.ic.identityToString(oid)

    def adv(self, proxy, current):
        self.instance.adv(proxy, current)
        if not self.enabled:
            return

        addr = self.get_idm_addr(proxy)
        self.pub.adv(addr)

    def bye(self, addr, current):
        self.instance.bye(addr, current)

        if not self.enabled:
            return

        self.pub.bye(addr)


class RouterServer(Ice.Application):
    def __init__(self):
        Ice.Application.__init__(self)

        self.ic = None
        self.adapter = None
        self.controller = None
        self.args = None
        self.__theend = None

    def run(self, args):
        if not self.parse_args(args[1:]):
            return 1

        if self.args.autokill is not None:
            self.__theend = AutoKill(self.args.autokill)

        self.ic = self.communicator()

        try:
            path = self.get_router_table_path(self.ic)
        except ValueError:
            logging.error(" property 'Router.Table.Path' not set")
            return 1

        # get this router's addresses and configure the routing table
        # with it (used to avoid loops)
        props = self.ic.getProperties()
        addresses = props.getProperty("Router.Ids")
        if addresses:
            addresses = addresses.split("|")

        table = RoutingTable(self.ic, path, addresses)

        self.adapter = self.ic.createObjectAdapter("Router.Adapter")
        self.adapter.activate()

        self.create_controller()
        proxies = self.register_servants(table)

        # NOTE: avoid publishing indirect proxies on Controller
        if proxies:
            oid = proxies[0].ice_getIdentity()
            router = self.adapter.createDirectProxy(oid)
            self.register_router(router)

        for p in proxies:
            logging.info(" router at '{}'".format(p))
        logging.info(" waiting events...")

        self.shutdownOnInterrupt()
        self.ic.waitForShutdown()
        logging.info(" shutting down...")

    def register_servants(self, table):
        srv = DUOAdvertiser(RouterI(table, self.controller, self.ic))
        proxies = []
        props = self.ic.getProperties()
        queue_size = props.getPropertyWithDefault("Router.QueueSize", "10")

        oids = props.getPropertyWithDefault("Router.Ids", "Router")
        for oid in oids.split("|"):
            if "/" in oid:
                oid = oid.split("/")[0]
            oid = self.ic.stringToIdentity(oid.strip())
            proxies.append(self.adapter.add(srv, oid))

        self.adapter.addDefaultServant(Forwarder(table, self.controller, queue_size), "")
        return proxies

    def create_controller(self):
        self.controller = self.ic.propertyToProxy("Router.Controller.Proxy")
        try:
            self.controller = IDM.ControllerPrx.checkedCast(self.controller)
        except Ice.Exception as ex:
            msg = str(ex).replace("\n", "\n" + 12 * " " + "> ")
            logging.warn(" could not contact with controller: " + msg)
            self.controller = None

        if not self.controller:
            logging.warn(" router controller not defined")
            return

    def register_router(self, proxy):
        if self.controller is None or proxy is None:
            return
        self.controller.newRouter(str(proxy))

    def parse_args(self, args):
        parser = ArgumentParser()
        parser.add_argument("--autokill", type=int, help="stops running after N seconds")

        try:
            self.args = parser.parse_args(args)
            return True
        except SystemExit:
            return False

    @staticmethod
    def get_router_table_path(ic):
        path = get_property(ic, "Router.Table.Path")
        if not os.path.exists(path):
            os.mknod(path)
        return path


class AutoKill(Thread):
    def __init__(self, timeout):
        Thread.__init__(self)
        self.daemon = True
        self.timeout = timeout
        self.start()

    def run(self):
        time.sleep(self.timeout)
        os.system('kill -9 {}'.format(os.getpid()))


if __name__ == '__main__':
    exit(RouterServer().main(sys.argv))
