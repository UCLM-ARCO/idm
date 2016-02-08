#!/usr/bin/env python
# -*- coding: utf-8; mode: python; -*-

import sys
import Ice


class Servant(Ice.Object):
    def __init__(self):
        self.c = 0

    def ice_ping(self, current):
        self.c += 1
        print "ice_ping():", self.c


class Server(Ice.Application):
    def run(self, args):
        ic = self.communicator()

        adapter = ic.createObjectAdapter("Adapter")
        adapter.activate()

        proxy = adapter.add(Servant(), ic.stringToIdentity("server"))

        print "Proxy: '{}'".format(proxy)
        self.shutdownOnInterrupt()
        ic.waitForShutdown()


if __name__ == '__main__':
    Server().main(sys.argv, "server.config")
