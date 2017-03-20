// -*- mode: c++; coding: utf-8 -*-

#include "SystemTools.h"

void blink(byte count, byte time) {
    for (byte i=0; i<count*2; i++) {
        digitalWrite(LED_BUILTIN, i%2);
        delay(time);
    }
}
