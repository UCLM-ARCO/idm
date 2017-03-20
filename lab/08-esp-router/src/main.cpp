// -*- mode: c++; coding: utf-8 -*-

#include <Arduino.h>
#include <ESP8266WiFi.h>

#include "SystemOTA.h"
#include "SystemTools.h"
#include "RouterServer.h"

#define WIFI_SSID "idm"

RouterServer router;

void setup() {
    // Initialize common settings
    Serial.begin(115200);
    delay(100);

    Serial.println("\nBooting...");
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, HIGH);

    // Setup WiFi communications
    Serial.println("Setting UP '" WIFI_SSID "' network");
    WiFi.softAP(WIFI_SSID);
    Serial.println("SoftAP IP address: 192.168.4.1");
    Serial.println("Ready");
    OTA::setup();
    blink(3, 50);

    // Initialize router operations
    router.begin();
}

void loop() {
    OTA::hanlde();
    router.loop_iteration();
}
