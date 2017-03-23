Overview
========

This example implements a simple TODO list, but providing two
interfaces: 1) using Ice and 2) using a HTTP REST api.

We must note that some adaptations must be made, because REST APIs are
designed to be used for CRUD operations, and ZeroC Ice is a Object
Oriented distributed middleware, with very different aims and scopes.


Limitations
===========

* Methods must return `void` or `string`, **only these
  allowed**. Rationale: once a parameter or struct is in binary
  format, it only could be reconstructed again using the slice, but
  the Endpoint (obviously) does not have the slice specification. In
  case you need to return some data or struct, use JSON format to
  serialize it.

* HTTP resources **must contain** object **identity** and **method**
  name. Usually, in a REST API you could use the same resource URL to
  perform different operations, depending on the used HTTP method. For
  instance, you could POST to '/todo/tasks' to create a new task, and
  GET to '/todo/tasks' to retrieve the list of current items. You can,
  also, use GET to '/todo/tasks/1' to retrieve the task with id=1, and
  PUT or DELETE to the same URL to update or remove the task. If you
  want to use this endpoint, the URL scheme must be change to take
  this into account. For example, you may use:

  * GET `/todo/getAll` --> `todo.getAll()`
  * GET `/todo/get/1` --> `todo.get(1)`
  * POST `/todo/add` + post data --> `todo.add(task)`
  * PUT `/todo/update/1` + post data --> `todo.update(task)`
  * DELETE `/todo/delete/1` --> `todo.delete(1)`


References
==========

This exaple is based on Miguel Grinberg's post about RESTful API's using flask:
https://blog.miguelgrinberg.com/post/designing-a-restful-api-with-python-and-flask
