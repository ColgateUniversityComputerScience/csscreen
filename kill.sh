#!/bin/bash

if [[ -f pid.txt ]]; then
    kill `cat pid.txt` 2>/dev/null
    sleep 2
    kill -9 `cat pid.txt` 2>/dev/null
    rm -f pid.txt
else
    echo "Screen display not running (no pid.txt file found)"
fi
