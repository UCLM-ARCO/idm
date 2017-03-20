// -*- mode: c++; coding: utf-8 -*-

#include <Arduino.h>
#include <ESP8266mDNS.h>
#include <EEPROM.h>
#include <ArduinoOTA.h>

#include "SystemOTA.h"

void OTA::setup() {
    bool led_state = LOW;
    ArduinoOTA.onStart([]() {
        Serial.println("Start");
    });
    ArduinoOTA.onEnd([]() {
        Serial.println("\nEnd");
        digitalWrite(LED_BUILTIN, HIGH);
    });
    ArduinoOTA.onProgress([&led_state](unsigned int progress, unsigned int total) {
        byte percentage = (progress / (total / 100));
        led_state = percentage % 2;
        digitalWrite(LED_BUILTIN, led_state);
        Serial.printf("Progress: %u%%\r", percentage);
    });
    ArduinoOTA.onError([](ota_error_t error) {
        Serial.printf("Error[%u]: ", error);
        if (error == OTA_AUTH_ERROR) Serial.println("Auth Failed");
        else if (error == OTA_BEGIN_ERROR) Serial.println("Begin Failed");
        else if (error == OTA_CONNECT_ERROR) Serial.println("Connect Failed");
        else if (error == OTA_RECEIVE_ERROR) Serial.println("Receive Failed");
        else if (error == OTA_END_ERROR) Serial.println("End Failed");
    });
    ArduinoOTA.begin();
}

void OTA::hanlde() {
    ArduinoOTA.handle();
}
