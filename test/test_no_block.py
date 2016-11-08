# -*- mode: python; coding: utf-8 -*-

import hamcrest
from prego import TestCase, Task


class TestReliability(TestCase):
    def test_router(self):
        count = 20

        # Note: the key here is that client does not block

        self.launch_router()
        self.launch_server(count)
        self.run_stress_client(count)

    def launch_router(self):
        router = Task(desc="IDM router", detach=True)
        cmd = router.command('src/router.py --Ice.Config=test/idm-router.config')
        router.assert_that(cmd.stderr.content, hamcrest.contains_string("adv from 'FA10 "))

    def launch_server(self, count):
        server = Task(desc="IDM server", detach=True)
        server.command("test/blocking-server.py --Ice.Config=test/server.config")

    def run_stress_client(self, count):
        client = Task(desc="IDM client")
        client.command(
            "test/multi-ice-ping-client.py FA10 {} --Ice.Config=test/client.config".format(count))
