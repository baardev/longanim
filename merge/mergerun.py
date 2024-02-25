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
if os.path.isfile("/tmp/STARTED"):
    os.unlink("/tmp/STARTED")
with open(f"images/mergerun.toml", 'r') as f:  C = toml.load(f)
#! kill any left over image viewiers and make a dummy image to teh view incase noe yet exit
# os.system("pkill vvv")
if os.path.isfile("/tmp/last.png") == False:
    os.system("convert -size 800x800 xc:white /tmp/last.png")

timetracker = {
    'qmasks': [0,0],
    'interpolate': [0, 0],
}

argv = sys.argv[1:]
try:
    opts, args = getopt.getopt(
        argv, "hf:t:c:",
        ['help',
         'from_image=',
         'to_image=',
         'counter='
         ],
    )
except Exception as e:
    print(str(e))


CURVE = C['curve']
W = C['w']
H = C['h']
PROJECT = C['project']
INTERPOLATE = C['interpolate']
IMAGE1 = False
IMAGE2 = False
counter = 0
total = 0
for opt, arg in opts:
    if opt in ("-f", "--from_image"): IMAGE1 = arg
    if opt in ("-t", "--to_image"): IMAGE2 = arg
    if opt in ("-c", "--counter"):
        ps = arg.split(":")
        counter = ps[0]
        total = ps[1]


STUB=f"{IMAGE1}_{IMAGE2}"
NAME=f"{STUB}.mp4"
FPS="30"  #! bump the fps tp 30
SECS=p.get_secs()
# p.prInfo("---------------------------------------------------")
# p.prInfo(f"export IMAGE1={IMAGE1}")
# p.prInfo(f"export IMAGE2={IMAGE2}")
# p.prInfo(f"export FPS={FPS}")
# p.prInfo(f"export W={W}")
# p.prInfo(f"export H={H}")
# p.prInfo(f"export PROJECT={PROJECT}")
# p.prInfo(f"export STUB={STUB}")
# p.prInfo(f"export NAME={STUB}")
# ^-----------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------------
# - Run 'mask_v0.json' workflow, which creates the interpolated frames
# -------------------------------------------------------------------------------------------
p.prInfo("┌─────────────────────────────────────────────")
p.prInfo(f"│ {counter}/{total}: MERGING")
p.prInfo("└─────────────────────────────────────────────")
# ! create frames
timetracker['qmasks'][0] = time.time()
CMD = f"""./qmasks_v0.py \
   --output_dir /home/jw/src/longanim/merge/stage_1/{PROJECT}/{STUB} \
   --input_dir /home/jw/src/longanim/merge/images \
   --images {IMAGE1}.png,{IMAGE2}.png \
   --curve {CURVE} \
   --res {W}:{H}
   """
p.prCmd(f"{CMD}")
os.system(CMD)
# ^ set target_weight to 0.5 to end at middle of interp
# ! need to wait for the que to finish by looking for the last filename created

final_filename = f"stage_1/{PROJECT}/{STUB}/*_1.00-0.00_00001_.png"
p.prAnn(f"Waiting for [{final_filename}]")
end = time.time()

start = time.time()
p.wait_for_glob(final_filename)
end = time.time()
p.prInfo(f"Total wait time: {end-start}")

timetracker['qmasks'][1] = time.time()
#PIL
# -------------------------------------------------------------------------------------------
# - Create main interps video
# -------------------------------------------------------------------------------------------
p.prInfo("┌─────────────────────────────────────────────")
p.prInfo("│ CREATE MAIN INTERPS VIDEO...")
p.prInfo("└─────────────────────────────────────────────")

timetracker['interpolate'][0]=time.time()
if os.path.exists(f"stage_2/{PROJECT}/{STUB}_00001.mp4"):
    p.prInfo(f"Using existing files in [stage_1/{PROJECT}/{STUB}]")
else:
# rm stage_3/${STUB}.mp4
    CMD = f"""./interpolate_v0.py \
      --name {STUB} \
      --input_dir stage_1/{PROJECT}/{STUB}/ \
      --output_dir stage_2/{PROJECT}/{STUB}/ \
      --frame_rate 8 \
      --multiplier 2 \
      --image_load_cap 1000 \
      --interpolate {INTERPOLATE}"""
p.prCmd(CMD)

os.system(CMD)

p.prInfo("┌─────────────────────────────────────────────")
p.prInfo("│ ...finished submitting queue")
p.prInfo("└─────────────────────────────────────────────")

p.wait_for_glob(f"stage_2/{PROJECT}/{STUB}/{STUB}_00001.mp4")
timetracker['interpolate'][1] = time.time()
#PIL
# ! if the file is big, needs time to finish writing
#  sleep 15
# ffmpeg -y -loglevel warning -i stage_2/${PROJECT}/${STUB}_00001.mp4 -filter:v fps=${FPS} stage_2/${PROJECT}/${FPS}_${STUB}_00001.mp4
# zip ${STUB}_MAIN.zip stage_2/*.png
#fi

# ! clean up unnecessary file
p.prInfo(f"Deleting PNG files in [stage_2/{PROJECT}/{STUB}]")
CMD=f"/bin/rm stage_2/{PROJECT}/{STUB}/*.png"
p.prCmd(CMD)
p.prunlive(CMD)

p.prInfo(f"Building 'list' in [stage_2/{PROJECT}/{STUB}]")
p.makelist(f"stage_2/{PROJECT}/list.txt",PROJECT)

p.prInfo(f"Merge files to [stage_2/{PROJECT}/{PROJECT}.mp4]")
# ! merge into 1 video

p.prInfo(f"READING: stage_2/{PROJECT}/list.txt")
p.prInfo(f"MERGING: stage_2/{PROJECT}/{PROJECT}.mp4")

CMD = f"ffmpeg -y -loglevel warning -f concat -safe 0 -i /home/jw/store/src/longanim/merge/stage_2/{PROJECT}/list.txt -c copy /home/jw/store/src/longanim/merge/stage_2/{PROJECT}/{PROJECT}.mp4"
p.prCmd(CMD)
p.prunlive(CMD)

p.prAnn("▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓")
p.prAnn(f"File ready at /home/jw/store/src/longanim/merge/stage_2/{PROJECT}/{PROJECT}.mp4")
p.prAnn("▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓")


for times in timetracker:
    # print(timetracker[times])
    delta = timetracker[times][1] - timetracker[times][0]
    p.prAnn(f"{times:20s}: {round(delta):06d} seconds")
