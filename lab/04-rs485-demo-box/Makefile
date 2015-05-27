# -*- mode: makefile-gmake; coding: utf-8 -*-

BOARD_TAG       = atmega328
ARDUINO_DIR     = /usr/share/arduino

USER_LIB_PATH   = $(HOME)/Arduino/libraries
PORT           ?= /dev/ttyUSB0
MONITOR_PORT    = $(PORT)
ARDUINO_LIBS    = TinkerKit IceC SoftwareSerial RRP RRPEndpoint
SLICE           = duo.ice

# CFLAGS          = -DDEBUG
# CFLAGS         += -DDEBUG_LED=13
CFLAGS         += -DADDR=$(ADDR)
CFLAGS         += -Wno-unused-function -Wno-unused-variable
CFLAGS         += -Wno-unused-but-set-variable -Wno-strict-aliasing
CXXFLAGS        = $(CFLAGS)

all: $(SLICE:%.ice=%.h)

upload-all:
	rm -f build-atmega328/*.o
	$(MAKE) upload PORT=/dev/ttyUSB0 ADDR=1
	rm -f build-atmega328/*.o
	$(MAKE) upload PORT=/dev/ttyUSB1 ADDR=2
	rm -f build-atmega328/*.o
	$(MAKE) upload PORT=/dev/ttyUSB2 ADDR=3

%.h: %.ice
	slice2c $^

vclean: clean
	rm -frv $(SLICE:%.ice=%.h)

include $(ARDUINO_DIR)/Arduino.mk
