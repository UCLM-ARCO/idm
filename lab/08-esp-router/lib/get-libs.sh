#!/bin/bash
# -*- mode: sh; coding: utf-8 -*-

echo -n "IceC... "
if [ ! -d IceC ]; then
    wget -q https://bitbucket.org/arco_group/icec/downloads/arduino-icec-latest.zip
    unzip -qq arduino-icec-latest.zip
    rm arduino-icec-latest.zip
    echo "[ok] "
else
    echo "[already present]"
fi
