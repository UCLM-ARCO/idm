#!/usr/bin/python -u
# -*- mode: python; coding: utf-8 -*-

import sys
import Ice

Ice.loadSlice("/usr/share/slice/duo/DUO.ice -I /usr/share/Ice/slice --all")
import DUO


class ListenerI(DUO.Listener):
    def adv(self, proxy, current):
        print "- adv from '{}'".format(proxy)


class Server(Ice.Application):
    def run(self, args):
        ic = self.communicator()

        adapter = ic.createObjectAdapter("Adapter")
        adapter.activate()

        adapter.add(ListenerI(), ic.stringToIdentity("Listener"))

        print "Waiting events..."
        self.shutdownOnInterrupt()
        ic.waitForShutdown()


if __name__ == '__main__':
    Server().main(sys.argv, "adv-listener.config")
