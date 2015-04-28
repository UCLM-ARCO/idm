// -*- mode: c++; coding: utf-8 -*-

#include <Arduino.h>
#include <MsTimer2.h>
#include <XBeeEndpoint.h>
#include <IceC/platforms/arduino/debug.hpp>

#include "user.h"

const byte led_pin = 5;
bool timedout = false;

Ice_Communicator ic;
Ice_ObjectAdapter adapter;
DUO_IBool_W servant;
Ice_ObjectPrx servant_proxy;
Ice_ObjectPrx adv_proxy;

void
DUO_IBool_WI_set(DUO_IBool_WPtr self, Ice_Bool v, DUO_Identity oid) {
    digitalWrite(led_pin, v);
}

// This is an IRS: keep it as short as possible
void
advertise() {
    timedout = true;
}

void
setup() {
    // Initialize broker and endpoint
    Ice_initialize(&ic);
    IceC_XBeeEndpoint_init(&ic);
    pinMode(13, OUTPUT);
    pinMode(led_pin, OUTPUT);

    digitalWrite(led_pin, HIGH);
    delay(500);
    digitalWrite(led_pin, LOW);

    const char* endps = "xbee -p idm -n server";
    const char* sep = " -d:";
    const char* oid = "Server";

    // Create object adapter
    Ice_Communicator_createObjectAdapterWithEndpoints
    	(&ic, "Adapter", endps, &adapter);
    Ice_ObjectAdapter_activate(&adapter);

    // Register servant
    DUO_IBool_W_init(&servant);
    Ice_ObjectAdapter_add(&adapter, (Ice_ObjectPtr)&servant, oid);

    // Create proxy to registered servant
    byte i = 0;
    char str_proxy[strlen(endps) + strlen(oid) + strlen(sep)];

    strcpy(str_proxy, oid);
    i += strlen(oid);
    strcpy(str_proxy + i, sep);
    i += strlen(sep);
    strcpy(str_proxy + i, endps);

    Ice_Communicator_stringToProxy
    	(&ic, str_proxy, &servant_proxy);

    // Create proxy to advertisement listener
    Ice_Communicator_stringToProxy
    	(&ic, "Listener -d:xbee -p idm -n listener", &adv_proxy);

    // Launch timer to advertise itself
    MsTimer2::set(2000, advertise);
    MsTimer2::start();
}

void
loop() {
    Ice_Communicator_loopIteration(&ic);

    if (!timedout)
    	return;

    digitalWrite(13, HIGH);
    DUO_Listener_adv(&adv_proxy, &servant_proxy);
    timedout = false;
    digitalWrite(13, LOW);
}
