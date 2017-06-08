#!/usr/bin/env python3

import subprocess
import os

BASEDIR = os.path.dirname(os.path.abspath(__file__))

cmdlist = [
    "cd {}".format(BASEDIR),
    "source xenv/bin/activate",
    "cd {}".format(os.path.join(BASEDIR, "controller")),
    "python3 manage.py runserver"
]
cmds = ';'.join(cmdlist)
print(cmds)

p = subprocess.Popen(cmds, shell=True, stdout=subprocess.PIPE)

try:
    p.wait()
except KeyboardInterrupt:
    p.terminate()

