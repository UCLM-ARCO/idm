// -*- mode: c++; coding: utf-8 -*-

#include <Arduino.h>
#include <ESP8266WiFi.h>

#include <IceC/platforms/esp8266/TCPEndpoint.h>
#include <IceC/platforms/esp8266/debug.hpp>

#include "RouterServer.h"

void
RouterServer::begin() {
    // IceC initialization
    Ice_initialize(&_ic);
    TCPEndpoint_init(&_ic);

    // Object adapter setup
    Ice_Communicator_createObjectAdapterWithEndpoints
        (&_ic, "Adapter", "tcp -p " ROUTER_PORT, &_adapter);
    Ice_ObjectAdapter_activate(&_adapter);

    // Install servants
    // Ice_ObjectAdapter_addDefaultServant
    //     (&_adapter, (Ice_ObjectPtr)&_forwarder);
}

void
RouterServer::loop_iteration() {
    Ice_Communicator_loopIteration(&_ic);
}
