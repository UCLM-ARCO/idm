#!/usr/bin/python -u
# -*- mode: python; coding: utf-8 -*-

import sys
import Ice

Ice.loadSlice("/usr/share/slice/idm/idm.ice")
import IDM


class Client(Ice.Application):
    def run(self, args):
        ic = self.communicator()

        router = ic.propertyToProxy("IDM.Router.Proxy")
        router = IDM.NeighborDiscovery.ListenerPrx.checkedCast(router)
        announced = "EEFF -t:tcp -h 127.0.0.1 -p 1234"

        print "Announced: '{}'".format(announced)
        router.adv(announced)


if __name__ == '__main__':
    args = sys.argv[:]

    has_config = False
    for i in args:
        if i.startswith("--Ice.Config="):
            has_config = True

    if not has_config:
        args.append('--Ice.Config=client.config')

    exit(Client().main(args))
