#!/usr/bin/python3 -u
# -*- mode: python3; coding: utf-8 -*-

import sys
import Ice

Ice.loadSlice("duo.ice")
import DUO


class Client(Ice.Application):
    def run(self, args):
        src = args[1]
        dst = self.get_node_proxy(args[2])
        dst.set(True, src)

    def get_node_proxy(self, dst):
        ic = self.communicator()
        router = ic.propertyToProxy("IDM.Router.Proxy")

        dst = ic.stringToIdentity(dst)
        dst = router.ice_identity(dst)
        return DUO.IBool.WPrx.uncheckedCast(dst)


if __name__ == "__main__":
    Client().main(sys.argv)
