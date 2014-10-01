#!/bin/bash
export DISPLAY=:0
./mkcert.sh 2>&1 >/dev/null
python3 screendisplay.py --fullscreen $*
