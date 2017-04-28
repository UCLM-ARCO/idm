#!/usr/bin/python3 -u
# -*- mode: python3; coding: utf-8 -*-

import sys
import Ice

Ice.loadSlice("idm.ice")
import IDM

Ice.loadSlice("duo.ice")
import DUO


class IBoolI(DUO.IBool.W):
    def set(self, state, source, current):
        print("set {} from {}".format(state, source))


class Node(Ice.Application):
    def run(self, args):
        self.idm_address = args[1]

        self.add_servant()
        self.register_on_router()
        self.event_loop()

    def add_servant(self):
        ic = self.communicator()

        adapter = ic.createObjectAdapter("Adapter")
        adapter.activate()

        oid = ic.stringToIdentity(self.idm_address)
        self.proxy = adapter.add(IBoolI(), oid)

        print("Proxy ready: '{}'".format(self.proxy))

    def register_on_router(self):
        ic = self.communicator()
        router = ic.propertyToProxy("IDM.Router.Proxy")
        router = IDM.NeighborDiscovery.ListenerPrx.checkedCast(router)

        router.adv(ic.proxyToString(self.proxy))

    def event_loop(self):
        ic = self.communicator()
        self.shutdownOnInterrupt()
        ic.waitForShutdown()


if __name__ == "__main__":
    Node().main(sys.argv)
