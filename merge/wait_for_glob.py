#!/bin/env python

import long_anim_lib as p
import time
import sys
from glob import glob

spec = sys.argv[1]
found = False
while found == False:
    files = glob(spec)
    if len(files) > 0:
        found = True
        print(f"Found [{spec}]")
        exit()
    else:
        print(f"Waiting for [{spec}]",flush=True)

    time.sleep(5)

