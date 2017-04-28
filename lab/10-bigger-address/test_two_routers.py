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
        self.run_node_1()
        self.run_client_to_node1()
        self.run_router_2()
        self.run_node_2()
        self.add_flows()
        # run client: n2.set()

    def clean(self):
        for path in ["router1.table", "router2.table"]:
            if os.path.exists(path):
                os.remove(path)

    def run_controller(self):
        controller = Task("IDM controller", detach=True)
        controller.command(
            "./idm-controller.py --Ice.Config=controller.config", expected=-15)

    def run_router_1(self):
        router1 = Task("IDM Router 1", detach=True)
        router1.command(
            "./router.py --Ice.Config=router1.config")

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
        router2_id = self.get_property("router2.config", "Router.Ids")




    def get_router_id(self, config, prop):
        with file(config) as f:
            for line in f.readlines():
                if line.strip().startswith(prop):
                    return line.split("=")[1].strip()
