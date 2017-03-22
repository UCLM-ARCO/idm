Overview
========

This example is based on Miguel Grinberg's post about RESTful API's using flask:
https://blog.miguelgrinberg.com/post/designing-a-restful-api-with-python-and-flask

It implements a simple TODO list, but using IDM as transport framework.

Limitations
===========

* Methods must return `void` or `string`, only these
  allowed. Rationale: once a parameter or struct is in binary format,
  it only could be reconstructed again using the slice, but the
  Endpoint (obviously) does not have the slice specification.

* No out params supported
