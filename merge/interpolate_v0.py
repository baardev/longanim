#!/bin/env python
import json
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
#!==================================================================================
p.prAnn("┌─────────────────────────────────────────────")
p.prAnn("│ ENTERED 'interpolate_v0.py'")
p.prAnn("└─────────────────────────────────────────────")
argv = sys.argv[1:]
opts = False
image_01 = False
image_02 = False
frame_rate = 30
multiplier = 4
image_load_cap = 103
interpolate = 2
lastclip = False
skip_first_images = 0

name = "unnamed"
try:
    opts, args = getopt.getopt(
        argv, "ho:i:n:F:M:I:J:L",
        [   'help',
                    'output_dir=',
                    'input_dir=',
                    'name=',
                    'frame_rate=',
                    'multiplier=',
                    'image_load_cap=',
                    'interpolate=',
                    'lastclip',
            ],
    )
except Exception as e:
    print(str(e))

input_dir = "/home/jw/src/longanim/merge/stage_1"
output_dir = "/home/jw/src/longanim/merge/stage_4"

for opt, arg in opts:
    if opt in ("-h", "--help"):p.showhelp()
    if opt in ("-o", "--output_dir"):output_dir = arg
    if opt in ("-i", "--input_dir"):input_dir = arg
    if opt in ("-n", "--name"):name = arg
    if opt in ("-F", "--frame_rate"): frame_rate = int(arg)
    if opt in ("-M", "--multiplier"):  multiplier = int(arg)
    if opt in ("-I", "--image_load_cap"):  image_load_cap = int(arg)
    if opt in ("-J", "--interpolate"):  interpolate = int(arg)
    if opt in ("-L", "--lastclip"):  lastclip = True

p.prInfo(f"Skipping ?")
if lastclip == True:
    files = glob(f"{input_dir}/*.png")
    skip_first_images = len(files) - 3
    p.prInfo(f"Skipping [{skip_first_images}] files")
# exit()
#! output from the START command
hideSTDOUT = "2>&1 >> /tmp/START.log"
p.prInfo("Restarting Server")
if output_dir != False:
    cmd = f"~/src/longanim/START -i {input_dir} -o {output_dir} {hideSTDOUT} &"
else:
    p.cleandir(output_dir)
    cmd = f"./START {hideSTDOUT} &"

p.prCmd(cmd)
os.system(cmd)
p.wait_for_server()

with open("interp_v0_API.json") as f:
    prompt = json.load(f)

p.prInfo(f"INPUT DIR: [{input_dir}]")
p.prInfo(f"OUTPUT VIDEO: [{output_dir}/{name}.mp4]")

prompt['3']['inputs']['frame_rate'] = frame_rate
prompt['3']['inputs']['filename_prefix'] = f"{name}"
prompt['4']['inputs']['multiplier'] = multiplier
prompt['5']['inputs']['interpolate'] = interpolate
prompt['1']['inputs']['image_load_cap'] = image_load_cap
prompt['1']['inputs']['directory'] = f"/home/jw/src/longanim/merge/{input_dir}"

# pprint(prompt)

from pprint import pprint
# pprint(prompt['1']['inputs'])

prompt['1']['inputs']['skip_first_images'] = skip_first_images


cmd = f"GPUMEMCLEAR"
p.prCmd(cmd)
p.prunlive(cmd)
cmd = f"~/src/longanim/START -o /home/jw/src/longanim/merge/{output_dir} -i /home/jw/src/longanim/merge/{input_dir} &"
p.prAnn("********************************************************************")
p.prCmd(cmd)
p.prAnn("********************************************************************")
os.system(cmd)
p.wait_for_server()

prompt_id = p.queue_prompt(prompt)['prompt_id']

p.prInfo("┌─────────────────────────────────────────────")
p.prInfo("│ EXITING 'interpolate_v0.py'")
p.prInfo("└─────────────────────────────────────────────")
