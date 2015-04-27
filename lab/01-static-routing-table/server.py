#!/usr/bin/python -u
# -*- mode: python; coding: utf-8 -*-

import sys
import Ice

Ice.loadSlice("/usr/share/slice/duo/DUO.ice -I /usr/share/Ice/slice --all")
import DUO


class IBoolWI(DUO.IBool.W):
    def set(self, value, oid, current):
        ic = current.adapter.getCommunicator()
        oid = ic.identityToString(oid)
        print "- set called, from '{}' with value '{}'".format(oid, value)


class Server(Ice.Application):
    def run(self, args):
        ic = self.communicator()

        adapter = ic.createObjectAdapter("Adapter")
        adapter.activate()

        adapter.add(IBoolWI(), ic.stringToIdentity("Server"))

        print "Waiting events..."
        self.shutdownOnInterrupt()
        ic.waitForShutdown()


if __name__ == '__main__':
    Server().main(sys.argv, "server.config")
