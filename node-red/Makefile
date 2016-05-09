# -*- mode: makefile-gmake; coding: utf-8 -*-

SLICE = duo_idm.ice

vpath %.ice /usr/share/slice/duo

all:

run: depends
	node-red -v

# NOTE: install locally, because I'm having trouble with global installation
depends: $(SLICE:%.ice=%.js)
	[ -d node_modules/ice ] || npm install ice

# NOTE: install slice2js with: "sudo npm -g install slice2js"
%.js: %.ice
	[ -d node_modules ] || mkdir node_modules
	slice2js --output-dir node_modules -I/usr/share/slice $^

	[ -d node_modules/idm ] || mkdir -p node_modules/idm
	slice2js --output-dir node_modules/idm /usr/share/slice/idm/idm.ice

.PHONY: clean
clean:
	$(RM) -vr *~ node_modules
