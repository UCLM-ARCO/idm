#!/usr/bin/python -u
# -*- mode: python; coding: utf-8 -*-

import sys
import Ice
from hexdump import hexdump


def get_property(ic, name):
    props = ic.getProperties()
    value = props.getProperty(name)
    if value == "":
        raise ValueError("Undefined property: '{}'".format(name))
    return value


class RoutingTable(object):
    def __init__(self, path):
        pass


class Router(Ice.Blobject):
    def __init__(self, ic):
        self.ic = ic

        path = get_property(ic, "Router.Table.Path")
        self.table = RoutingTable(path)

    def ice_invoke(self, bytes, current):
        print "ice_invoke", current.operation,
        hexdump(bytes)

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
