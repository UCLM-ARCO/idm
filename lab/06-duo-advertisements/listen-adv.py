#!/usr/bin/python -u
# -*- mode: python; coding: utf-8 -*-

import sys
import Ice
import IceStorm

Ice.loadSlice("/usr/share/slice/duo/duo_idm.ice -I/usr/share/slice --all")
import DUO


class ListenerI(DUO.IDM.Listener):
    def adv(self, addr, current):
        addr = self.get_printable_addr(addr)
        print "- adv from '{}'".format(addr)

    def get_printable_addr(self, addr):
        return "".join([hex(ord(x))[2:] for x in addr])


class Server(Ice.Application):
    def run(self, args):
        self.ic = self.communicator()

        adapter = self.ic.createObjectAdapterWithEndpoints("Adapter", "tcp")
        adapter.activate()

        subs = adapter.addWithUUID(ListenerI())
        self.subscribe_to_topic(subs)

        print "Waiting events..."
        self.shutdownOnInterrupt()
        self.ic.waitForShutdown()

    def subscribe_to_topic(self, proxy, topic_name="announce"):
        mgr = self.ic.propertyToProxy("IceStorm.TopicManager.Proxy")
        mgr = IceStorm.TopicManagerPrx.checkedCast(mgr)

        try:
            topic = mgr.retrieve(topic_name)
        except IceStorm.NoSuchTopic:
            topic = mgr.create(topic_name)

        topic.subscribeAndGetPublisher({}, proxy)


if __name__ == '__main__':
    args = sys.argv[:]

    has_config = False
    for i in args:
        if i.startswith("--Ice.Config="):
            has_config = True

    if not has_config:
        args.append('--Ice.Config=client.config')

    Server().main(args)
