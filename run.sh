#!/bin/bash

cd /home/pi/csscreen

export DISPLAY=:0

# wake screen up and make it stay on
xset s noblank
xset s off # don't activate screensaver
xset -dpms # disable DPMS (Energy Star) features.

./mkcert.sh 2>/dev/null
python3 screendisplay.py --fullscreen $*
