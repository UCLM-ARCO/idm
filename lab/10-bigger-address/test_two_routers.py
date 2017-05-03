# -*- mode: python; coding: utf-8 -*-

import os
from prego import TestCase, Task
from hamcrest import contains_string


class TestTwoRouters(TestCase):
    NODE1_ADDR = "BBAA10"
    NODE2_ADDR = "BBCC0020"
    CLIENT_ADDR = "FFCC10"

    def test_run(self):

        self.clean()
        self.run_controller()
        self.run_router_1()
        self.run_client_to_unknown_node()

        self.run_node_1()
        self.run_client_to_node1()

        self.run_router_2()
        self.run_node_2()
        self.add_flows()
        self.run_client_to_node2()

    def clean(self):
        for path in ["router1.table", "router2.table"]:
            if os.path.exists(path):
                os.remove(path)

    def get_property(self, config, prop):
        with file(config) as f:
            for line in f.readlines():
                if line.strip().startswith(prop):
                    return line.split("=")[1].strip()

    def run_controller(self):
        controller = Task("IDM controller", detach=True)
        controller.command(
            "./idm-controller.py --Ice.Config=controller.config", expected=-15)

    def run_router_1(self):
        router1_t = Task("IDM Router 1", detach=True)
        self.router1 = router1_t.command(
            "./router.py --Ice.Config=router1.config")

    def run_client_to_unknown_node(self):
        dst = "123455"
        client = Task("Client to Unknown Node")
        client.command(
            "./client.py --Ice.Config=client.config {} {}".format(self.CLIENT_ADDR, dst))

        client.assert_that(
            self.router1.stderr.content,
            contains_string("no route to '{}'".format(dst))
        )

    def run_node_1(self):
        node1_t = Task("Node 1", detach=True)
        self.node1 = node1_t.command(
            "./node.py --Ice.Config=node1.config {}".format(self.NODE1_ADDR))

    def run_client_to_node1(self):
        client = Task("Client to Node 1")
        client.command(
            "./client.py --Ice.Config=client.config {} {}".format(self.CLIENT_ADDR, self.NODE1_ADDR))

        client.assert_that(
            self.node1.stdout.content,
            contains_string("set True from {}".format(self.CLIENT_ADDR))
        )

    def run_router_2(self):
        router2 = Task("IDM Router 2", detach=True)
        router2.command(
            "./router.py --Ice.Config=router2.config")

    def run_node_2(self):
        node2_t = Task("Node 2", detach=True)
        self.node2 = node2_t.command(
            "./node.py --Ice.Config=node2.config {}".format(self.NODE2_ADDR))

    def add_flows(self):
        router1_prx = self.get_property("node1.config", "IDM.Router.Proxy")
        router2_prx = self.get_property("node2.config", "IDM.Router.Proxy")
        rule = self.NODE2_ADDR[:4] + "/112"
        admin = Task("Add flows")
        admin.command(
            "./admin.py '{}' add {} '{}'".format(router1_prx, rule, router2_prx))

    def run_client_to_node2(self):
        client = Task("Client to Node 2")
        client.command(
            "./client.py --Ice.Config=client.config {} {}".format(self.CLIENT_ADDR, self.NODE2_ADDR))

        client.assert_that(
            self.node2.stdout.content,
            contains_string("set True from {}".format(self.CLIENT_ADDR))
        )
