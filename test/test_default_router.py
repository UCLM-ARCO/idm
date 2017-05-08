# -*- mode: python; coding: utf-8 -*-

import hamcrest
from prego import TestCase, Task


class TestDefaultRouter(TestCase):
    def test_run(self):
        count = 50

        self.create_router_table()
        self.launch_router()
        self.launch_server(count)
        self.run_stress_client(count)

    def create_router_table(self):
        with file("test/idm-router.table", "w") as table:
            route = "00 | 120 | FF01 | tcp -h 127.0.0.1 -p 7890 | t"
            table.write(route)

    # router address: FF01
    def launch_router(self):
        router = Task(desc="IDM router", detach=True)
        cmd = router.command('src/router.py --Ice.Config=test/idm-router.config')
        router.assert_that(
            cmd.stderr.content, hamcrest.contains_string("forward to 'FA10 "))

    # server address: FA10
    def launch_server(self, count):
        server = Task(desc="IDM server", detach=True)
        cmd = server.command(
            "test/count-ice-ping-server.py --no-adv --Ice.Config=test/server.config")
        expected_msg = "ice_ping called {} times".format(count)
        server.assert_that(cmd.stdout.content, hamcrest.contains_string(expected_msg))

    # client using addreess: FA10 but router's endpoints
    def run_stress_client(self, count):
        client = Task(desc="IDM client")
        client.command(
            "test/multi-ice-ping-client.py FA10 {} --Ice.Config=test/client.config".format(
                count))
