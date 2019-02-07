#!/usr/bin/python3 -u
# -*- mode: python3; coding: utf-8 -*-

import os
import sys
import Ice

pwd = os.path.abspath(os.path.dirname(__file__))
Ice.loadSlice("{}/../src/idm.ice")
import IDM

Ice.loadSlice("{}/ibool.ice".format(pwd))
import DUO


class IBoolI(DUO.IBool.W):
    def set(self, state, source, current):
        print("set {} from {}".format(state, source))


class Node(Ice.Application):
    def run(self, args):
        self.transient = False
        self.idm_address = ""
        self.parse_args(args)

        self.add_servant()
        self.register_on_router()
        self.event_loop()
        self.unregister_from_router()

    def parse_args(self, args):
        for k in args[1:]:
            if k == "--transient":
                self.transient = True
            else:
                self.idm_address = k

    def add_servant(self):
        ic = self.communicator()

        adapter = ic.createObjectAdapter("Adapter")
        adapter.activate()

        oid = ic.stringToIdentity(self.idm_address)
        self.proxy = adapter.add(IBoolI(), oid)

        print("Proxy ready: '{}'".format(self.proxy))

    def register_on_router(self):
        ic = self.communicator()
        self.router = ic.propertyToProxy("IDM.Router.Proxy")
        self.router = IDM.NeighborDiscovery.ListenerPrx.checkedCast(self.router)
        self.router.adv(ic.proxyToString(self.proxy))

    def unregister_from_router(self):
        ic = self.communicator()
        self.router.bye(ic.identityToString(self.proxy.ice_getIdentity()))

    def event_loop(self):
        if not self.transient:
            ic = self.communicator()
            self.shutdownOnInterrupt()
            ic.waitForShutdown()


if __name__ == "__main__":
    Node().main(sys.argv)
