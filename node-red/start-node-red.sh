#!/bin/bash

while true; do
    node-red -v &
    PID=$!
    inotifywait -e modify,create,delete *;
    kill $PID
done
