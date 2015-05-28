#!/usr/bin/python -u
# -*- mode: python; coding: utf-8 -*-

import sys
import Ice

from libidm import Broker

Ice.loadSlice("/usr/share/slice/duo/DUO.ice -I /usr/share/Ice/slice --all")
import DUO


class Client(Ice.Application):
    def run(self, args):
        ic = self.communicator()
        idm = Broker(ic)

        state = args[2] != "0"

        remote = idm.getProxy(args[1])
        remote = DUO.IBool.WPrx.uncheckedCast(remote)
        remote.set(state, Ice.Identity())


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print "Usage: {} <addr> <0|1>".format(sys.argv[0])
        exit(1)

    exit(Client().main(sys.argv, "client.config"))
