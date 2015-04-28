#!/usr/bin/python -u
# -*- mode: python; coding: utf-8 -*-

import sys
import os
import Ice
from threading import Lock

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
        self.lock = Lock()
        self.routes = {}

        with file(path) as src:
            self.proccess_file(src)

    def add(self, destination, endpoints):
        with self.lock:
            self.routes[destination] = endpoints

    def proccess_file(self, src):
        for line in src:
            line = line.strip()
            if line.startswith(":"):
                continue

            destination, endpoints = map(str.strip, line.split("\t"))
            self.add(destination, endpoints)

    def get_next(self, oid):
        oid = self.ic.identityToString(oid)
        endps = self.routes.get(oid, None)
        if endps is None:
            raise NoSuchRoute

        return self.ic.stringToProxy("{} -o:{}".format(oid, endps))


class Router(Ice.Blobject):
    def __init__(self, table):
        self.table = table

    # FIXME: make table persisten
    def __del__(self):
        pass

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
        self.table.add(destination, endpoints)


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
