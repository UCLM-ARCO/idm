#!/usr/bin/env python
# -*- coding: utf-8; mode: python; -*-

import sys
import Ice


class Client(Ice.Application):
    def run(self, args):
        ic = self.communicator()

        proxy = ic.stringToProxy("Server -t:tcp -h 127.0.0.1 -p 2000")

        print "Using proxy: '{}'".format(proxy)
        for i in range(1000):
            proxy.ice_ping()


if __name__ == '__main__':
    Client().main(sys.argv)
