#!/usr/bin/python3 -u
# -*- mode: python; coding: utf-8 -*-

import sys
import Ice

Ice.loadSlice("todo.ice")
import ToDo


class ListI(ToDo.List):
    def __init__(self):
        self.tasks = {}

    def getAll(self, current):
        print(" - getAll()")
        return list(self.tasks.values())

    def get(self, task_id, current):
        print(" - get({})".format(task_id))
        return self.tasks[task_id]

    def add(self, task, current):
        print(" - add({})".format(self.str_task(task)))
        self.tasks[task.id] = task

    def update(self, task, current):
        print(" - update({})".format(task))
        self.tasks[task.id] = task

    def delete(self, task_id, current):
        print(" - delete({})".format(task_id))
        self.tasks.pop(task_id)

    def str_task(self, task):
        return "<id: {}, title: '{}', desc: '{}', done: {}>".format(
            task.id,
            task.title[:10] + "..." if len(task.title) > 10 else task.title,
            task.description[:10] + "..." if len(task.description) > 10 else task.description,
            task.done)


class Server(Ice.Application):
    def run(self, args):
        ic = self.communicator()

        adapter = ic.createObjectAdapter("Adapter")
        adapter.activate()

        servant_id = ic.stringToIdentity("TODO")
        proxy = adapter.add(ListI(), servant_id)
        print("Server: '{}'".format(proxy))

        self.shutdownOnInterrupt()
        ic.waitForShutdown()


if __name__ == "__main__":
    Server().main(sys.argv, "server.config")
