#!/bin/bash
# -*- mode: sh; coding: utf-8 -*-

TERM="gnome-terminal"

function launch-server() {
    local address=$1
    local position=$2

    local cmd="$(pwd)/server.py $address"
    local options=" --hide-menubar -e '$cmd' --geometry $position"

    eval $TERM $options
}


offset=$1
[[ -n "$offset" ]] || offset=0

launch-server 2.2 80x15+$offset+0
launch-server 2.3 80x15+$offset+330
launch-server 2.4 80x15+$offset+660
