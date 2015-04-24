# -*- mode: makefile-gmake; coding: utf-8 -*-

# Arduino FIO
BOARD_TAG     = fio
ARDUINO_DIR   = /usr/share/arduino
MONITOR_PORT  = /dev/ttyUSB0

# You need the icec repo on user libraries dir
USER_LIB_PATH = $(HOME)/Arduino/libraries
ARDUINO_LIBS  = IceC XBeeEndpoint EasyXBee XBee SoftwareSerial
SLICE         = user.ice

CFLAGS       += -DDEBUG_LED=13
CFLAGS       += -Wno-unused-function -Wno-unused-variable
CFLAGS       +=	-Wno-unused-but-set-variable -Wno-strict-aliasing
CXXFLAGS      = $(CFLAGS)


all: $(SLICE:%.ice=%.h)

%.h: %.ice
	slice2c $^

.PHONY: vclean
vclean: clean
	rm -frv $(SLICE:%.ice=%.h)

include $(ARDUINO_DIR)/Arduino.mk
