#!/usr/bin/python -u
# -*- mode: python; coding: utf-8 -*-

import os
import sys
import Ice
import IceStorm
from Queue import Queue, Full
from argparse import ArgumentParser
from threading import RLock, Thread
import logging

logging.getLogger().setLevel(logging.INFO)


def load_slice(name, parent=""):
    path = os.path.join(os.path.dirname(__file__), name)
    if not os.path.exists(path):
        path = "/usr/share/slice/{}{}".format(parent, name)

    Ice.loadSlice("{} -I{} -I/usr/share/slice --all".format(path, Ice.getSliceDir()))

load_slice("idm.ice", "idm/")
load_slice("duo_idm.ice", "duo/")
import IDM
import DUO


def get_property(ic, name):
    props = ic.getProperties()
    value = props.getProperty(name)
    if value == "":
        raise ValueError("Undefined property: '{}'".format(name))
    return value


class NoSuchRoute(Exception):
    pass


class RoutingTable(object):
    def __init__(self, ic, path):
        self.ic = ic
        self.path = path
        self.lock = RLock()
        self.routes = {}

        with file(path) as src:
            self.proccess_file(src)

    def add(self, destination, endpoints, mode):
        with self.lock:
            id = self.get_id_for(destination)
            self.routes[destination] = (endpoints, mode, id)

            # FIXME: store in a separate thread, once each 5 mins (or so)
            self.store()

    def remove(self, destination):
        with self.lock:
            try:
                self.routes.pop(destination)

                # FIXME: store in a separate thread, once each 5 mins (or so)
                self.store()
            except KeyError:
                pass

    def remove_by_id(self, id):
        with self.lock:
            dst = self.find_by_id(id)
            if dst is None:
                return None, None

            info = self.routes[dst]
            self.remove(dst)
            return dst, info

    def find_by_id(self, id):
        with self.lock:
            for dst, info in self.routes.items():
                if info[2] == id:
                    return dst

    def get_id_for(self, destination):
        try:
            id = self.routes[destination][2]
        except KeyError:
            id = 0
            for r in self.routes.values():
                id = max(id, r[2])
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
                destination, endpoints, mode = map(str.strip, line.split(" | "))
                self.add(destination, endpoints, mode)
            except Exception:
                logging.warn("Invalid line on routing table, ignoring...")

    def store(self):
        header = ": DO NOT EDIT, it will be overwritten!\n"
        header += ": destination | endpoints | mode\n: " + "-" * 50 + "\n"
        with file(self.path, "w") as dst:
            dst.write(header)
            for destination in sorted(self.routes.keys()):
                info = self.routes[destination]
                line = "{} | {} | {}\n".format(destination, *info)
                dst.write(line)

    def get_next(self, oid):
        oid = self.ic.identityToString(oid)
        route = self.routes.get(oid, None)

        # try to get router for that specific network
        if route is None:
            netid = oid[:2] + "*"
            route = self.routes.get(netid, None)

        # or try to get the default router
        if route is None:
            route = self.routes.get("*", None)

        if route is None:
            raise NoSuchRoute

        endps, mode = route[0], route[1]
        proxy = self.ic.stringToProxy("{} -{}:{}".format(oid, mode, endps))
        proxy = proxy.ice_encodingVersion(Ice.Encoding_1_0)
        return proxy


class IncommingMessage(object):
    def __init__(self, in_params, current):
        self.oid = current.id
        self.operation = current.operation
        self.mode = current.mode
        self.ctx = current.ctx.copy()
        self.in_params = buffer(in_params[:])


class Forwarder(Ice.Blobject):
    def __init__(self, table, queue_size=10):
        self.table = table
        self.queue = Queue(maxsize=queue_size)
        logging.info("Queue Size: {}".format(queue_size))

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
            logging.error("- could not forward message: full queue!")

        return True, buffer("")

    def forwarder_loop(self):
        while True:
            msg = self.queue.get()
            self.process_message(msg)
            self.queue.task_done()

    def process_message(self, msg):
        try:
            next = self.table.get_next(msg.oid)
            logging.info("- forward to '{}'".format(next))
            next.ice_invoke(msg.operation, msg.mode, msg.in_params, msg.ctx)

        except NoSuchRoute:
            oid = Ice.identityToString(msg.oid)
            logging.error("- no route to '{}'".format(oid))
        except Ice.Exception as e:
            logging.error("- could not forward message: " + str(e))


class RouterI(IDM.Router):
    def __init__(self, table, ic):
        self.table = table
        self.ic = ic

    def flowAdd(self, flow, current):
        destination = self.address_to_string(flow.m.dst)

        # add default route
        if destination == "0000":
            destination = "*"

        # or add route for whole network
        elif destination[2:] == "00":
            destination = destination[:2] + "*"

        try:
            _, endpoints, mode = self.get_proxy_info(flow.a.next)
        except Ice.Exception as e:
            logging.error("- could not add flow: " + str(e))
            return

        logging.info("- flowAdd for '{}', dst: {}".format(destination, flow.a.next))
        self.table.add(destination, endpoints, mode)

    def flowDelete(self, identifier, current):
        dst, info = self.table.remove_by_id(identifier)
        rule = " not exists!"
        if dst is not None:
            rule = ": {} | {} | {}".format(dst, info[0], info[1])
        logging.info("- flowDelete of {}, rule{}".format(identifier, rule))

    def flowList(self, current):
        logging.info("- flowList done")
        flows = []

        rows = self.table.list()
        for destination, info in rows.items():
            if destination == "*":
                destination = "0000"
            addr = self.string_to_address(destination.replace("*", "00"))
            matcher = IDM.Routing.Matcher(addr)
            nextHop = "R -{}:{}".format(info[1], info[0])
            action = IDM.Routing.Action(IDM.Routing.ActionType.Forward, nextHop)
            flow = IDM.Routing.Flow(info[2], matcher, action)
            flows.append(flow)

        return flows

    def adv(self, proxy, current):
        try:
            destination, endpoints, mode = self.get_proxy_info(proxy)
        except Ice.Exception as e:
            logging.error("- invalid adv: " + str(e))
            return

        logging.info("- adv from '{}'".format(proxy))
        self.table.add(destination, endpoints, mode)

    def bye(self, oid, current):
        stroid = self.address_to_string(oid)
        logging.info("- bye from '{}'".format(stroid))
        self.table.remove(oid)

    def get_proxy_info(self, proxy):
        fields = proxy.split(" ")
        destination = fields[0].replace(":", "").strip('"').upper()
        if "*" in destination:
            fields[0] = "dummy"

        proxy = " ".join(fields)
        proxy = self.ic.stringToProxy(proxy)
        endpoints = ":".join(map(str, proxy.ice_getEndpoints()))

        mode = "t"
        if proxy.ice_isDatagram():
            mode = "d"
        elif proxy.ice_isOneway():
            mode = "o"

        return destination, endpoints, mode

    def address_to_string(self, a):
        return "".join(["{:02X}".format(c) for c in map(ord, a)])

    def string_to_address(self, s):
        s = s.replace(":", "").strip('"')
        fields = [s[i:i + 2] for i in range(0, len(s), 2)]
        return "".join(chr(int(b, 16)) for b in fields)


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
            logging.warn("DUO advertisements disabled")
            return

        try:
            topic = mgr.retrieve(topic_name)
        except IceStorm.NoSuchTopic:
            topic = mgr.create(topic_name)

        pub = topic.getPublisher().ice_datagram()
        try:
            pub.ice_ping()
        except Ice.NoEndpointException:
            logging.warn("DUO advertisements disabled")
            return

        self.enabled = True
        return DUO.IDM.ListenerPrx.uncheckedCast(pub)

    def get_idm_addr(self, str_proxy):
        proxy = self.ic.stringToProxy(str_proxy)
        oid = proxy.ice_getIdentity()
        oid = self.ic.identityToString(oid)
        addr = [int(oid[0:2], 16), int(oid[2:4], 16)]
        return addr

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
    def run(self, args):
        if not self.parse_args(args[1:]):
            return 1

        if self.args.autokill is not None:
            self.__theend = AutoKill(self.args.autokill)

        ic = self.communicator()

        try:
            path = self.get_router_table_path(ic)
        except ValueError:
            logging.error("Property 'Router.Table.Path' not set")
            return 1

        table = RoutingTable(ic, path)

        adapter = ic.createObjectAdapter("Router.Adapter")
        adapter.activate()

        srv = DUOAdvertiser(RouterI(table, ic))
        proxies = []
        props = ic.getProperties()
        queue_size = props.getPropertyWithDefault("Router.QueueSize", "10")
        oids = props.getPropertyWithDefault("Router.Ids", "Router")

        for oid in oids.split("|"):
            oid = ic.stringToIdentity(oid.strip())
            proxies.append(adapter.add(srv, oid))
        adapter.addDefaultServant(Forwarder(table, queue_size), "")

        for p in proxies:
            logging.info("Router at '{}'".format(p))
        logging.info("Waiting events...")
        self.shutdownOnInterrupt()
        ic.waitForShutdown()
        logging.info("Shutting down...")

    def parse_args(self, args):
        parser = ArgumentParser()
        parser.add_argument("--autokill", type=int, help="stops running after N seconds")

        try:
            self.args = parser.parse_args(args)
            return True
        except SystemExit:
            return False

    def get_router_table_path(self, ic):
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
        import time
        time.sleep(self.timeout)
        os.system('kill -9 {}'.format(os.getpid()))


if __name__ == '__main__':
    exit(RouterServer().main(sys.argv))
