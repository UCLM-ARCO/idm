#!/usr/bin/env python
# -*- coding: utf-8; mode: python; -*-

import sys
import Ice


class Servant(Ice.Object):
    def ice_ping(self, current):
        print "PING CALLED"


class Server(Ice.Application):
    def run(self, args):
        ic = self.communicator()
        adapter = ic.createObjectAdapterWithEndpoints(
            "Adapter", "tcp -h 127.0.0.1 -p 2001")
        adapter.activate()

        proxy = adapter.add(Servant(), ic.stringToIdentity("Server"))
        print "Proxy ready: '{}'".format(proxy)

        print "Waiting events..."
        self.shutdownOnInterrupt()
        ic.waitForShutdown()


if __name__ == '__main__':
    Server().main(sys.argv)
