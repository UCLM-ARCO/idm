#!/usr/bin/python -u
# -*- mode: python; coding: utf-8 -*-

import sys
import os
import Ice
from threading import Lock

# For DUO.Listener interface (node advertisements)
Ice.loadSlice("/usr/share/slice/duo/DUO.ice -I /usr/share/Ice/slice --all")
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

    def proccess_file(self, src):
        for line in src:
            line = line.strip()
            if line.startswith(":"):
                continue

            try:
                destination, endpoints, mode = map(str.strip, line.split(" | "))
                self.add(destination, endpoints, mode)
            except Exception:
                print "WARNING: Invalid line on routing table, ignoring..."

    def store(self):
        header = ": destination | endpoints | mode\n: " + "-" * 50 + "\n"
        with file(self.path, "w") as dst:
            dst.write(header)
            for destination, info in self.routes.items():
                line = "{} | {} | {}\n".format(destination, *info)
                dst.write(line)

    def get_next(self, oid):
        oid = self.ic.identityToString(oid)
        route = self.routes.get(oid, None)
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

    def ice_invoke(self, bytes, current):
        try:
            next = self.table.get_next(current.id)
            print "- forward to '{}'".format(next)
            next.ice_invoke(current.operation, current.mode, bytes)
        except NoSuchRoute:
            ic = current.adapter.getCommunicator()
            oid = ic.identityToString(current.id)
            print "- ERROR: no route to '{}'".format(oid)

        return True, buffer("")


class ListenerI(DUO.Listener):
    def __init__(self, table):
        self.table = table

    def adv(self, proxy, current):
        print "- adv from '{}'".format(proxy)
        ic = current.adapter.getCommunicator()
        destination = ic.identityToString(proxy.ice_getIdentity())
        endpoints = ":".join(map(str, proxy.ice_getEndpoints()))

        mode = "t"
        if proxy.ice_isDatagram():
            mode = "d"
        elif proxy.ice_isOneway():
            mode = "o"

        self.table.add(destination, endpoints, mode)


class RouterServer(Ice.Application):
    def run(self, args):
        ic = self.communicator()

        path = self.get_router_table_path(ic)
        table = RoutingTable(ic, path)

        adapter = ic.createObjectAdapter("Router.Adapter")
        adapter.activate()
        proxy = adapter.add(ListenerI(table), ic.stringToIdentity("Router"))
        adapter.addDefaultServant(Router(table), "")

        print "Router at '{}'".format(proxy)

        print "Waiting events..."
        self.shutdownOnInterrupt()
        ic.waitForShutdown()

    def get_router_table_path(self, ic):
        path = get_property(ic, "Router.Table.Path")
        if not os.path.exists(path):
            os.mknod(path)
        return path


if __name__ == '__main__':
    exit(RouterServer().main(sys.argv, "router.config"))
