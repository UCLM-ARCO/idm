# -*- mode: python; coding: utf-8 -*-

import hamcrest
from prego import TestCase, Task


class TestReliability(TestCase):
    def test_router(self):
        count = 1000

        self.launch_router()
        self.launch_server(count)
        self.run_stress_client(count)

    def launch_router(self):
        router = Task(desc="IDM router", detach=True)
        cmd = router.command('src/router.py --Ice.Config=test/idm-router.config')
        router.assert_that(
            cmd.stderr.content, hamcrest.contains_string("adv from 'FA10 "))

    def launch_server(self, count):
        server = Task(desc="IDM server", detach=True)
        cmd = server.command(
            "test/count-ice-ping-server.py --Ice.Config=test/server.config")
        expected_msg = "ice_ping called {} times".format(count)
        server.wait_that(
            cmd.stdout.content, hamcrest.contains_string(expected_msg))

    def run_stress_client(self, count):
        client = Task(desc="IDM client")
        client.command(
            "test/multi-ice-ping-client.py FA10 {} --Ice.Config=test/client.config".format(
                count))
