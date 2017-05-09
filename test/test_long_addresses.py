# -*- mode: python; coding: utf-8 -*-

import os
from prego import TestCase, Task
from hamcrest import contains_string


def get_property(config, prop):
    with file(config) as f:
        for line in f.readlines():
            if line.strip().startswith(prop):
                return line.split("=")[1].strip()


class TestAddressing(TestCase):
    CLIENT_ADDR = "FFCC10"
    NODE_ADDR = [
        "123456",
        "BBAA10",
        "BBCC0020",
        "22AA45130",
    ]

    def setUp(self):
        self.clean()
        self.run_controller()

    def test_direct_deliver_of_unknown_node(self):
        self.run_router(1)
        self.run_client_to_missing_node(0, 'r1')

    def test_direct_delivery(self):
        self.run_router(1)
        self.run_node(1, "server_r1")
        self.run_client_to_node(1, 'r1')

    def test_indirect_delivery(self):
        self.run_router(1)
        self.run_router(2)
        self.run_node(2, "server_r2")
        self.add_flow('r1', self.NODE_ADDR[2] + "/120", 'r2')
        self.run_client_to_node(2, 'r1')

    def test_bye_of_node_can_not_reach_it_again(self):
        self.run_router(1)
        self.run_node(3, 'server_r1', transient=True)
        self.run_client_to_missing_node(3, 'r1')

    def test_forward_to_bigger_netmask(self):
        self.run_router(1)
        self.run_router(2)
        self.run_router(3)
        self.run_node(3, "server_r3")
        self.add_flow('r1', self.NODE_ADDR[3] + "/118", 'r2')
        self.add_flow('r1', self.NODE_ADDR[3] + "/121", 'r3')
        self.add_flow('r1', self.NODE_ADDR[3] + "/115", 'r2')
        self.run_client_to_node(3, 'r1')

    def test_default_route_0_as_netmask(self):
        self.run_router(1)
        self.run_router(2)
        self.add_flow('r1', "0/0", 'r2')
        self.run_node(1, 'server_r2')
        self.run_client_to_node(1, 'r1')

    # -- below are just helper methods ---------------------------------------------

    def clean(cls):
        for path in ["router1.table", "router2.table", "controller-saved-state.bin"]:
            if os.path.exists(path):
                os.remove(path)

    def run_controller(self):
        controller = Task("IDM controller", detach=True)
        controller.command(
            "idm-controller --Ice.Config=test/controller.config", expected=-15)

    def run_router(self, index):
        router_t = Task("IDM Router {}".format(index), detach=True)
        router = router_t.command(
            "src/router.py --Ice.Config=test/router{}.config".format(index))
        setattr(self, "router_r{}".format(index), router)

    def run_node(self, index, router, transient=False):
        node_t = Task("Node {}".format(index), detach=True)
        node = node_t.command(
            "test/ibool-server.py {} --Ice.Config=test/{}.config {}".format(
                "--transient" if transient else "",
                router, self.NODE_ADDR[index]))
        setattr(self, "node{}_t".format(index), node_t)
        setattr(self, "node{}".format(index), node)

    def add_flow(self, src, rule, dst):
        router1_prx = get_property("test/server_{}.config".format(src), "IDM.Router.Proxy")
        router2_prx = get_property("test/server_{}.config".format(dst), "IDM.Router.Proxy")
        admin = Task("Add flows {} -> {}".format(src, dst))
        admin.command(
            "src/admin.py '{}' add {} '{}'".format(router1_prx, rule, router2_prx))

    def run_client_to_node(self, index, router):
        client = Task("Client to Node {}".format(index))
        client.command(
            "test/ibool-client.py --Ice.Config=test/client_{}.config {} {}".format(
                router, self.CLIENT_ADDR, self.NODE_ADDR[index]))

        node = getattr(self, "node{}".format(index))
        client.assert_that(
            node.stdout.content,
            contains_string("set True from {}".format(self.CLIENT_ADDR))
        )

    def run_client_to_missing_node(self, index, router):
        client = Task("Client to Node {} (which is missing)".format(index))
        client.command(
            "test/ibool-client.py --Ice.Config=test/client_{}.config {} {}".format(
                router, self.CLIENT_ADDR, self.NODE_ADDR[index]))

        router = getattr(self, "router_{}".format(router))
        client.assert_that(
            router.stderr.content,
            contains_string("no route to '{}'".format(self.NODE_ADDR[index]))
        )
