#!/usr/bin/python -u
# -*- mode: python; coding: utf-8 -*-

import os
import sys
import Ice
import IceStorm
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
            try:
                id = self.routes[destination][2]
            except KeyError:
                id = len(self.routes)
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
            dst = self.find_id(id)
            if dst is None:
                return None, None

            info = self.routes[dst]
            self.remove(dst)
            return dst, info

    def find_id(self, id):
        with self.lock:
            for dst, info in self.routes.items():
                if info[2] == id:
                    return dst

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

        if route is None:
            netid = oid[:2] + "*"
            route = self.routes.get(netid, None)

        if route is None:
            raise NoSuchRoute

        endps, mode = route[0], route[1]
        proxy = self.ic.stringToProxy("{} -{}:{}".format(oid, mode, endps))
        proxy = proxy.ice_encodingVersion(Ice.Encoding_1_0)
        return proxy


class Forwarder(Ice.Blobject):
    def __init__(self, table):
        self.table = table

    def __del__(self):
        self.table.store()

    def ice_invoke(self, in_params, current):
        try:
            next = self.table.get_next(current.id)
            logging.info("- forward to '{}'".format(next))
            return next.ice_invoke(
                current.operation, current.mode, in_params, current.ctx)
        except NoSuchRoute:
            ic = current.adapter.getCommunicator()
            oid = ic.identityToString(current.id)
            logging.error("- no route to '{}'".format(oid))

        except Ice.Exception as e:
            logging.error("- could not forwared message: " + str(e))

        return True, buffer("")


class RouterI(IDM.Router):
    def __init__(self, table, ic):
        self.table = table
        self.ic = ic

    def flowAdd(self, flow, current):
        destination = self.address_to_string(flow.m.dst)

        # add route for whole network
        if destination[2:] == "00":
            destination = destination[:2] + "*"

        _, endpoints, mode = self.get_proxy_info(flow.a.next)

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
            addr = self.string_to_address(destination.replace("*", "00"))
            matcher = IDM.Routing.Matcher(addr)
            nextHop = "R -{}:{}".format(info[1], info[0])
            action = IDM.Routing.Action(IDM.Routing.ActionType.Forward, nextHop)
            flow = IDM.Routing.Flow(info[2], matcher, action)
            flows.append(flow)

        return flows

    def adv(self, proxy, current):
        destination, endpoints, mode = self.get_proxy_info(proxy)

        logging.info("- adv from '{}'".format(proxy))
        self.table.add(destination, endpoints, mode)

    def bye(self, oid, current):
        stroid = self.address_to_string(oid)
        logging.info("- bye from '{}'".format(stroid))
        self.table.remove(oid)

    def get_proxy_info(self, proxy):
        fields = proxy.split(" ")
        destination = fields[0]
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
        return "{:02X}{:02X}".format(*map(ord, a))

    def string_to_address(self, s):
        s = s.replace(":", "")
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

        # do not advertise default routes
        if "*" in proxy.split(" ")[0]:
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
        oids = ic.getProperties().getPropertyWithDefault("Router.Ids", "Router")
        for oid in oids.split("|"):
            oid = ic.stringToIdentity(oid.strip())
            proxies.append(adapter.add(srv, oid))
        adapter.addDefaultServant(Forwarder(table), "")

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
