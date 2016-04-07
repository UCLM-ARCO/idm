#!/usr/bin/python -u
# -*- mode: python; coding: utf-8 -*-

import os
import sys
import Ice
import IceStorm
from threading import Lock, Thread
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
        self.lock = Lock()
        self.routes = {}

        with file(path) as src:
            self.proccess_file(src)

    def add(self, destination, endpoints, mode):
        with self.lock:
            self.routes[destination] = (endpoints, mode)

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

    def proccess_file(self, src):
        for line in src:
            line = line.strip()
            if line.startswith(":"):
                continue

            try:
                destination, endpoints, mode = map(str.strip, line.split(" | "))
                self.add(destination, endpoints, mode)
            except Exception:
                logging.warn("WARNING: Invalid line on routing table, ignoring...")

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

        if route is None:
            netid = oid[:2] + "*"
            route = self.routes.get(netid, None)

        if route is None:
            raise NoSuchRoute

        endps, mode = route[0], route[1]
        proxy = self.ic.stringToProxy("{} -{}:{}".format(oid, mode, endps))
        proxy = proxy.ice_encodingVersion(Ice.Encoding_1_0)
        return proxy


class Router(Ice.Blobject):
    def __init__(self, table):
        self.table = table

    def __del__(self):
        self.table.store()

    def ice_invoke(self, in_params, current):
        try:
            next = self.table.get_next(current.id)
            logging.info("forward to '{}'".format(next))
            return next.ice_invoke(
                current.operation, current.mode, in_params, current.ctx)
        except NoSuchRoute:
            ic = current.adapter.getCommunicator()
            oid = ic.identityToString(current.id)
            logging.error("no route to '{}'".format(oid))

        return True, buffer("")


class ListenerI(IDM.NeighborDiscovery.Listener):
    def __init__(self, table):
        self.table = table

    def adv(self, proxy, current):
        logging.info("adv from '{}'".format(proxy))

        fields = proxy.split(" ")
        destination = fields[0]
        if "*" in destination:
            fields[0] = "dummy"

        proxy = " ".join(fields)
        ic = current.adapter.getCommunicator()
        proxy = ic.stringToProxy(proxy)
        endpoints = ":".join(map(str, proxy.ice_getEndpoints()))

        mode = "t"
        if proxy.ice_isDatagram():
            mode = "d"
        elif proxy.ice_isOneway():
            mode = "o"

        self.table.add(destination, endpoints, mode)

    def bye(self, oid, current):
        stroid = "{:02X}{:02X}".format(*map(ord, oid))
        logging.info("bye from '{}'".format(stroid))
        self.table.remove(oid)


# A Wrapper, to maintain it decoupled
class DUOAdvertiser(IDM.NeighborDiscovery.Listener):
    def __init__(self, listener, ic):
        self.listener = listener
        self.ic = ic
        self.enabled = False
        self.pub = self.get_publisher("announce")

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
        self.listener.adv(proxy, current)

        if not self.enabled:
            return

        # do not advertise default routes
        if "*" in proxy.split(" ")[0]:
            return

        addr = self.get_idm_addr(proxy)
        self.pub.adv(addr)

    def bye(self, addr, current):
        self.listener.bye(addr, current)

        if not self.enabled:
            return

        self.pub.bye(addr)


class RouterServer(Ice.Application):
    def run(self, args):
        if "--autokill" in args:
            timeout = int(args[args.index("--autokill") + 1])
            self.__theend = AutoKill(timeout)

        ic = self.communicator()

        path = self.get_router_table_path(ic)
        table = RoutingTable(ic, path)

        adapter = ic.createObjectAdapter("Router.Adapter")
        adapter.activate()

        oid = ic.getProperties().getPropertyWithDefault("Router.Id", "Router")
        oid = ic.stringToIdentity(oid)
        srv = DUOAdvertiser(ListenerI(table), ic)
        proxy = adapter.add(srv, oid)
        adapter.addDefaultServant(Router(table), "")

        logging.info("Router at '{}'".format(proxy))
        logging.info("Waiting events...")
        self.shutdownOnInterrupt()
        ic.waitForShutdown()
        logging.info("Shutting down...")

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
