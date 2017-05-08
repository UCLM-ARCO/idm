# -*- mode: makefile-gmake; coding: utf-8 -*-

DESTDIR ?= ~

all:

install:
	install -d $(DESTDIR)/usr/bin
	install -m 555 src/router.py $(DESTDIR)/usr/bin/idm-router
	install -m 555 src/admin.py $(DESTDIR)/usr/bin/idm-admin

	> src/router.table
	install -d $(DESTDIR)/usr/share/idm/example
	install -m 444 src/router.config $(DESTDIR)/usr/share/idm/example
	install -m 444 src/router.table $(DESTDIR)/usr/share/idm/example

	install -d $(DESTDIR)/usr/share/slice/idm/
	install -m 444 src/idm.ice $(DESTDIR)/usr/share/slice/idm/

	install -d $(DESTDIR)/usr/share/pyshared/idm/
	install -m 444 src/libidm.py $(DESTDIR)/usr/share/pyshared/idm/
	> $(DESTDIR)/usr/share/pyshared/idm/__init__.py


.PHONY: test clean
test: OPTS ?= -eo
test:
	-prego $(OPTS) test/test_*.py

clean:
	$(MAKE) -C lab/08-esp-router/ $@
	find -name "*.pyc" -print -delete
