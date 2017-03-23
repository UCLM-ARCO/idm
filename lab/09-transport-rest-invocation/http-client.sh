#!/bin/bash
# -*- mode: sh; coding: utf-8 -*-

CT_JSON="Content-Type: application/json"
URL="http://127.0.0.1:8000/TODO"
# OPS="-i"


# ACTIONS: list
echo -ne "\n - items:\n     "
curl $URL/getAll $OPS

# ACTIONS: add, list
echo -ne "\n - add task 1:\n     "
task1='{"id": 1, "title": "Add task using curl", "description": "None.", "done": true}'
curl -H "$CT_JSON" -X POST -d "$task1" $URL/add $OPS
curl $URL/getAll $OPS

# ACTIONS: update, get
echo -ne "\n - update task 1:\n     "
changes='{"id": 1, "title": "Add task using curl", "description": "None.", "done": false}'
curl -H "$CT_JSON" -X PUT -d "$changes" $URL/update $OPS
curl $URL/get/1 $OPS

# ACTIONS: remove, list
echo -ne "\n - remove task 1:\n     "
curl -X DELETE $URL/delete/1 $OPS
curl $URL/getAll $OPS
