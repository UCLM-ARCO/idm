#!/usr/bin/python3 -u
# -*- mode: python; coding: utf-8 -*-

import sys
import Ice
import json
from pprint import pprint

Ice.loadSlice("todo.ice")
import ToDo


class Client(Ice.Application):
    def run(self, args):
        ic = self.communicator()

        if len(args) < 2:
            print("Usage: {} <proxy>".format(args[0]))
            return 1

        todo_list = ic.stringToProxy(args[1])
        todo_list = ToDo.ListPrx.uncheckedCast(todo_list)

        # ACTIONS: list
        self.print_tasks(todo_list)

        # ACTIONS: add, list
        print(" - add task 1")
        task1 = ToDo.Task(1, "Travel to Mars", "Go to Mars and enjoy it!", False)
        todo_list.add(task1)
        self.print_tasks(todo_list)

        # ACTIONS: update, list
        print(" - update task 1")
        task1.done = True
        todo_list.add(task1)
        self.print_tasks(todo_list)

        # ACTIONS: remove, list
        # print(" - remove task 1")
        # todo_list.delete(task1.id)
        # self.print_tasks(todo_list)

    def print_tasks(self, todo_list):
        items = json.loads(todo_list.getAll())
        print(" - items: ")
        pprint(items, indent=4)


if __name__ == "__main__":
    Client().main(sys.argv)
