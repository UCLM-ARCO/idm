#!/usr/bin/python -u
# -*- mode: python; coding: utf-8 -*-

import sys
import Ice


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
        self.routes = {}

        with file(path) as src:
            self.proccess_file(src)

    def proccess_file(self, src):
        for line in src:
            line = line.strip()
            if line.startswith(":"):
                continue

            destination, endpoints = map(str.strip, line.split("\t"))
            self.routes[destination] = endpoints

    def get_next(self, oid):
        oid = self.ic.identityToString(oid)
        endps = self.routes.get(oid, None)
        if endps is None:
            raise NoSuchRoute

        return self.ic.stringToProxy("{} -o:{}".format(oid, endps))


class Router(Ice.Blobject):
    def __init__(self, ic):
        self.ic = ic

        path = get_property(ic, "Router.Table.Path")
        self.table = RoutingTable(ic, path)

    def ice_invoke(self, bytes, current):
        next = self.table.get_next(current.id)
        print "- forward to '{}'".format(next)

        next.ice_invoke(current.operation, current.mode, bytes)

        return True, buffer("")


class RouterServer(Ice.Application):
    def run(self, args):
        ic = self.communicator()

        adapter = ic.createObjectAdapter("Router.Adapter")
        adapter.activate()
        adapter.addDefaultServant(Router(ic), "")

        print "Waiting events..."
        self.shutdownOnInterrupt()
        ic.waitForShutdown()


if __name__ == '__main__':
    exit(RouterServer().main(sys.argv, "router.config"))
