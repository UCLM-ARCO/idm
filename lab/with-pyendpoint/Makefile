# -*- mode: makefile-gmake; coding: utf-8 -*-

SHELL = /bin/bash
# ROUTER = idm-router
ROUTER = /home/oscar/repos/idm/src/router.py

all:

run-router: gen-table
	export PYTHONPATH=$$(pwd); \
	$(ROUTER) --Ice.Config=router.config

run-client:
	./client.py $(COUNT)

run-server:
	./server.py

gen-table:
	echo "0001 | xendp | d" > router.table
	echo "0002 | udp -h 127.0.0.1 -p 1234 | d" >> router.table
