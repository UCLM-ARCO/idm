# -*- mode: makefile-gmake; coding: utf-8 -*-

DESTDIR ?= ~

all:

install:
	install -d $(DESTDIR)/usr/bin
	install -m 555 src/router.py $(DESTDIR)/usr/bin/idm-router

	install -d $(DESTDIR)/usr/share/idm-embedded/example
	install -m 444 src/router.config $(DESTDIR)/usr/share/idm-embedded/example
	install -m 444 src/router.table $(DESTDIR)/usr/share/idm-embedded/example
