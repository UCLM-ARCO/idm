#!/usr/bin/env python
# -*- coding: utf-8; mode: python; -*-

import sys
import Ice


class Servant(Ice.Blobject):
    def __init__(self, next):
        self.counter = 1
        self.next = next

    def ice_invoke(self, in_params, current):
        print "ice_invoke called ({})".format(self.counter)
        self.counter += 1

        next = self.next.ice_identity(current.id)

        # NOTE: vital to pass context as forth param!
        return next.ice_invoke(
            current.operation, current.mode, in_params, current.ctx)


class Server(Ice.Application):
    def run(self, args):
        ic = self.communicator()
        endp = "tcp -h 127.0.0.1 -p 2000"
        adapter = ic.createObjectAdapterWithEndpoints(
            "Adapter", endp)
        adapter.activate()

        next = ic.stringToProxy("X -t:tcp -h 127.0.0.1 -p 2001")
        adapter.addDefaultServant(Servant(next), "")

        print "Forwarder ready at: '{}'".format(endp)
        print "Waiting events..."
        self.shutdownOnInterrupt()
        ic.waitForShutdown()


if __name__ == '__main__':
    Server().main(sys.argv)
