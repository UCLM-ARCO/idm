// -*- mode: c++; coding: utf-8 -*-

#include <Arduino.h>
#include <TinkerKit.h>
#include <IceC/IceC.h>
// #include <IceC/platforms/arduino/debug.hpp>
#include <RRPEndpoint.h>

#include <duo.h>

TKButton button(I0);
TKLed light(O0);

Ice_Communicator ic;
Ice_ObjectAdapter adapter;
Ice_ObjectPrx remote;
DUO_IBool_W servant;


void
DUO_IBool_WI_set(DUO_IBool_WPtr self, Ice_Bool v, DUO_Identity oid) {
    v ? light.on() : light.off();
}

void
setup() {
    // debug_init();
    Serial.begin(115200);

    // Initialize Ice and register RRP endpoint
    Ice_initialize(&ic);
    IceC_RRPEndpoint_init(&ic);

    // Create object adapter
    char endp[11];
    sprintf(endp, "rrp -a %d", ADDR);

    Ice_Communicator_createObjectAdapterWithEndpoints
	(&ic, "Adapter", endp, &adapter);
    Ice_ObjectAdapter_activate(&adapter);

    // Register servant with proper identity
    char servant_id[6];
    sprintf(servant_id, "1.%d", ADDR);

    DUO_IBool_W_init(&servant);
    Ice_ObjectAdapter_add(&adapter, (Ice_ObjectPtr)&servant, servant_id);

    // Create proxy to remote object
    char strprx[18];
    char addresses[3][4] = {"1.3", "2.2", "2.3"};
    char* dst = addresses[ADDR - 2 % 3];
    sprintf(strprx, "%s -d:rrp -a 1", dst);

    Ice_Communicator_stringToProxy(&ic, strprx, &remote);
}

void
loop() {
    static bool oldState = false;
    bool newState = button.readSwitch();

    // If button state has changed, send the message
    if (newState != oldState) {
	// Ice_String name;
	// Ice_String_init(name, "Sarah");

	// Example_Hello_helloFrom(&remote, name);
	// oldState = newState;
	// digitalWrite(DEBUG_LED, newState);
    }

    // // This endpoint in particular needs some housekeeping to be done,
    // // in client mode, this method will do it
    // IceC_RRPEndpoint_tick();
}
