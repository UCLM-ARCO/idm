#!/usr/bin/env python
# -*- coding: utf-8; mode: python; -*-

import sys
import Ice


class Client(Ice.Application):
    def run(self, args):
        ic = self.communicator()

        remote = ic.propertyToProxy("IDM.Router.Proxy")
        remote = remote.ice_identity(ic.stringToIdentity("0001"))

        c = int(sys.argv[1]) if len(sys.argv) > 1 else 1
        for i in range(int(c)):
            remote.ice_ping()


if __name__ == '__main__':
    Client().main(sys.argv, "client.config")
