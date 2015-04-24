// -*- mode: c++; coding: utf-8 -*-

#include <Arduino.h>
#include <XBeeEndpoint.h>
#include <IceC/platforms/arduino/debug.hpp>

#include "user.h"

const int sensorPin = 2;
volatile bool intRaised = false;

Ice_Communicator ic;
Ice_ObjectPrx remote;

void
isr() {
    intRaised = true;
}

void
setup() {
    Ice_initialize(&ic);
    IceC_XBeeEndpoint_init(&ic);

    Ice_Communicator_stringToProxy
    	(&ic, "Server -d:xbee -p idm -n router", &remote);

    attachInterrupt(0, isr, CHANGE);
}

void
loop() {
    if (!intRaised)
     	return;

    intRaised = false;
    bool state = digitalRead(sensorPin);

    DUO_Identity oid;
    Ice_String_init(oid.name, "sensor");
    Ice_String_init(oid.category, "");

    DUO_IBool_W_set(&remote, state, oid);
}
