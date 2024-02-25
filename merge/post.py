#!/bin/env python
import json
import subprocess

import long_anim_lib as p
from pathlib import Path
from itertools import count, takewhile
import os
import sys
import getopt
from random import random
from random import seed
import time
import tempfile
from glob import glob
from pprint import pprint
import toml
import shutil


#!==================================================================================
os.chdir("/home/jw/src/longanim/merge/")
with open(f"images/mergerun.toml", 'r') as f:  C = toml.load(f)
#! kill any left over image viewiers and make a dummy image to teh view incase noe yet exit

timetracker = {
    'upscale': [0,0],
    'ffinterpolate': [0, 0],
}

PROJECT = C['project']

# ^-----------------------------------------------------------------------------------------


#! always upscale first
timetracker['upscale'][0] = time.time()
if C['upscale'] == 2 or C['upscale'] == 4:
    p.prInfo(f"Upscaling by {C['upscale']}")
    cmd=f"""/home/jw/src/longanim/simple_upscale_video.sh \
    /home/jw/store/src/longanim/merge/stage_2/{PROJECT}/{PROJECT}.mp4 \
    {C['upscale']} \
    /home/jw/store/src/longanim/merge/stage_2/{PROJECT}"""

    p.prCmd(cmd)
    os.system(cmd)
    p.wait_for_glob(f"/home/jw/store/src/longanim/merge/stage_2/{PROJECT}/{PROJECT}_out.mp4",quite=True)

else:
    p.prInfo(f"Skipping upscale (=|{C['upscale']}|")

timetracker['upscale'][1] = time.time()


timetracker['ffinterpolate'][0] = time.time()
if C['ffinterpolate'] != 0:
    p.prInfo(f"Interpolating (ffmpeg) to |{C['ffinterpolate']} fps")
    cmd=f"""ffmpeg \
    -y -loglevel warning \
    -hwaccel cuda \
    -i /home/jw/store/src/longanim/merge/stage_2/{PROJECT}/{PROJECT}.mp4 \
    -crf 20 \
    -vf minterpolate=fps={C['ffinterpolate']}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1 \
    /home/jw/store/src/longanim/merge/stage_2/{PROJECT}/{PROJECT}_out{C['ffinterpolate']}fps.mp4"""

    p.prCmd(cmd)
    os.system(cmd)
    p.wait_for_glob(f"/home/jw/store/src/longanim/merge/stage_2/{PROJECT}/{PROJECT}_out{C['ffinterpolate']}fps.mp4", quite=True)

else:
    p.prInfo(f"Skipping upscale (=|{C['upscale']}|")

timetracker['ffinterpolate'][1] = time.time()

for times in timetracker:
    # print(timetracker[times])
    delta = timetracker[times][1] - timetracker[times][0]
    p.prAnn(f"{times:20s}: {round(delta):06d} seconds")

