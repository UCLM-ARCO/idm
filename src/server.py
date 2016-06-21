#!/usr/bin/env python
# -*- mode: python; coding: utf-8 -*-

import sys
import Ice

Ice.loadSlice("idm.ice")
import IDM


class ServantI(Ice.Object):
    def __init__(self):
        self.counter = 0

    def ice_ping(self, current):
        self.counter += 1
        print "ice_ping called {} times".format(self.counter)


class Server(Ice.Application):
    def run(self, args):
        ic = self.communicator()

        adapter = ic.createObjectAdapter("Adapter")
        adapter.activate()

        oid = ic.getProperties().getProperty("IDM.Address")
        prx = adapter.add(ServantI(), ic.stringToIdentity(oid))
        self.register_on_router(prx)
        print "Proxy: '{}'".format(prx)

        print "Waiting events..."
        self.shutdownOnInterrupt()
        ic.waitForShutdown()

    def register_on_router(self, proxy):
        ic = self.communicator()
        router = ic.propertyToProxy("IDM.Router.Proxy")
        router = IDM.NeighborDiscovery.ListenerPrx.checkedCast(router)

        router.adv(ic.proxyToString(proxy))


if __name__ == "__main__":
    Server().main(sys.argv)
