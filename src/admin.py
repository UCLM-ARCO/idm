#!/usr/bin/env python3
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
        netmask = 15
        if "/" in addr:
            addr, netmask = addr.split("/")
            try:
                netmask = int(netmask)
                assert netmask >= 0 and netmask <= 128
            except (ValueError, AssertionError):
                raise ValueError("Invalid netmask value, should be a number in range [0,128]")

        matcher = IDM.Routing.Matcher(addr, netmask)
        action = IDM.Routing.Action(IDM.Routing.ActionType.Forward, self.args.route)
        flow = IDM.Routing.Flow(0, matcher, action)
        self.router.flowAdd(flow)

    def cmd_list(self):
        flows = self.router.flowList()
        if not flows:
            print("No flows")
            return

        print(" #ID | Address | Destination\n" + "-" * 60)
        for f in sorted(flows, key=lambda x: x.identifier):
            print("{: 4d}:   {}  ->  {}".format(f.identifier, f.m.address, f.a.next))

    def cmd_delete(self):
        self.router.flowDelete(self.args.flowid)

    def string_to_address(self, s):
        return s.replace(":", "").strip()

    def create_proxies(self):
        ic = self.communicator()
        router = ic.stringToProxy(self.args.router)
        self.router = IDM.RouterPrx.uncheckedCast(router)

    def parse_args(self, args):
        parser = ArgumentParser()
        parser.add_argument("router", help="router where execute the action")
        subparsers = parser.add_subparsers(dest="action")

        parser_add = subparsers.add_parser("add", help="add a new flow")
        parser_add.add_argument("address", help="matching address (use /nnn for netmask)")
        parser_add.add_argument("route", help="next hop on route")

        subparsers.add_parser("list", help="list current flows")

        parser_delete = subparsers.add_parser("delete", help="remove specified flow")
        parser_delete.add_argument("flowid", type=int, help="flow identifier")

        try:
            self.args = parser.parse_args(args)
            return True
        except SystemExit:
            return False


if __name__ == '__main__':
    exit(IDMAdmin().main(sys.argv))
