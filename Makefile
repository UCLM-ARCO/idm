# -*- mode: makefile-gmake; coding: utf-8 -*-

DESTDIR ?= ~

all:

install:
	install -d $(DESTDIR)/usr/bin
	install -m 555 src/router.py $(DESTDIR)/usr/bin/idm-router
	install -m 555 src/admin.py $(DESTDIR)/usr/bin/idm-admin

	install -d $(DESTDIR)/usr/share/slice/idm/
	install -m 444 src/idm.ice $(DESTDIR)/usr/share/slice/idm/

.PHONY: tests clean
tests: OPTS ?= -eo
tests:
	-prego $(OPTS) test/test_*.py

clean:
	$(MAKE) -C lab/08-esp-router/ $@
	find -name "*.pyc" -print -delete
