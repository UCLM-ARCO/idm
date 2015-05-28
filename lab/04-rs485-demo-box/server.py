#!/usr/bin/python -u
# -*- mode: python; coding: utf-8 -*-

import sys
import Ice

Ice.loadSlice("duo.ice")
import DUO


class IBoolWI(DUO.IBool.W):
    def set(self, state, oid, current):
        print(" -> event .set({}, Ice.Identity('{}'))".format(state, oid.name))


class Server(Ice.Application):
    def run(self, args):
        ic = self.communicator()

        port = 9000 + int(args[1].split(".")[-1])
        adapter = ic.createObjectAdapterWithEndpoints(
            "Adapter", "tcp -h 127.0.0.1 -p {}".format(port))
        adapter.activate()

        proxy = adapter.add(IBoolWI(), ic.stringToIdentity(args[1]))
        print "Server ready at '{}'".format(proxy)

        self.shutdownOnInterrupt()
        ic.waitForShutdown()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "Usage: {} <addr>".format(sys.argv[0])
        exit(1)

    Server().main(sys.argv)
