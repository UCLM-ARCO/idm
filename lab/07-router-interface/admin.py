#!/usr/bin/env python
# -*- mode: python; coding: utf-8 -*-

import os
import sys
import Ice
from argparse import ArgumentParser


def load_slice(name, parent=""):
    path = os.path.join(os.path.dirname(__file__), name)
    if not os.path.exists(path):
        path = "/usr/share/slice/{}{}".format(parent, name)

    Ice.loadSlice("{} -I{} -I/usr/share/slice --all".format(path, Ice.getSliceDir()))

load_slice("idm.ice", "idm/")
import IDM


class IDMAdmin(Ice.Application):
    def run(self, args):
        if not self.parse_args(args[1:]):
            return 1

        self.create_proxies()
        self.perform_action()

    def perform_action(self):
        cmd = getattr(self, "cmd_" + self.args.action)
        cmd()

    def cmd_add(self):
        addr = self.string_to_address(self.args.address)
        matcher = IDM.Routing.Matcher(addr)
        action = IDM.Routing.Action(IDM.Routing.ActionType.Forward, self.args.route)
        self.router.flowModify(matcher, action)

    def string_to_address(self, s):
        s = s.replace(":", "")
        fields = [s[i:i + 2] for i in range(0, len(s), 2)]
        return "".join(chr(int(b, 16)) for b in fields)

    def create_proxies(self):
        ic = self.communicator()
        router = ic.stringToProxy(self.args.router)
        self.router = IDM.RouterPrx.uncheckedCast(router)

    def parse_args(self, args):
        parser = ArgumentParser()
        parser.add_argument("router", help="router where execute the action")
        subparsers = parser.add_subparsers(dest="action")

        parser_action = subparsers.add_parser("add", help="add a new rule")
        parser_action.add_argument("address", help="network address to match")
        parser_action.add_argument("route", help="next hop to forward messages")

        try:
            self.args = parser.parse_args(args)
            return True
        except SystemExit:
            return False


if __name__ == '__main__':
    exit(IDMAdmin().main(sys.argv))
