#!/usr/bin/env python
# -*- mode: python; coding: utf-8 -*-

import sys
import Ice


class Client(Ice.Application):
    def run(self, args):
        if len(args) != 3:
            print "Usage: {} <dst> <count>".format(args[0])
            return -1

        ic = self.communicator()
        router = ic.propertyToProxy("IDM.Router.Proxy")
        dst = ic.stringToIdentity(args[1])
        dst = router.ice_identity(dst)

        for i in range(int(args[2])):
            dst.ice_ping()


if __name__ == "__main__":
    Client().main(sys.argv)
