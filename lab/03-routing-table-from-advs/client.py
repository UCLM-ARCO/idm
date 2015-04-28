#!/usr/bin/python -u
# -*- mode: python; coding: utf-8 -*-

import sys
import Ice

Ice.loadSlice("/usr/share/slice/duo/DUO.ice -I /usr/share/Ice/slice --all")
import DUO


class Client(Ice.Application):
    def run(self, args):
        ic = self.communicator()

        remote = ic.stringToProxy(args[1])
        remote = DUO.IBool.WPrx.uncheckedCast(remote)

        state = args[2] != "0"
        oid = ic.stringToIdentity("client")
        remote.set(state, oid)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "Usage: {} <proxy> <0|1>".format(sys.argv[0])
        exit(1)

    Client().main(sys.argv)
