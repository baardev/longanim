#!/bin/env python
import json
import long_anim_lib as p
from pathlib import Path
from itertools import count, takewhile
import os
import sys
import getopt

def frange(start, stop, step):
    tnary = []
    nary = takewhile(lambda x: x < stop, count(start, step))
    for i in list(nary):
        tnary.append(round(i,2))
    # print(tnary)
    return tnary

#!==================================================================================

argv = sys.argv[1:]
opts = False
image_01 = False
image_02 = False
try:
    opts, args = getopt.getopt(
        argv, "ho:i:p:r:t:",
        [   'help',
                    'output_dir=',
                    'input_dir=',
                    'images=',
                    'res=',
                    'target_weight=',
            ],
    )
except Exception as e:
    print(str(e))

output_dir = False
input_dir = False
res = "512:512"
width = 512
height = 512
target_weight = 1.0

for opt, arg in opts:
    if opt in ("-h", "--help"):p.showhelp()
    if opt in ("-o", "--output_dir"):output_dir = arg
    if opt in ("-i", "--input_dir"):input_dir = arg
    if opt in ("-r", "--res"):
        res = arg
        parts = str(arg).split(":")
        width = parts[0]
        height = parts[1]
    if opt in ("-p", "--images"):
        itmp = str(arg).split(",")
        print("--",itmp)
        image_01 = itmp[0]
        image_02 = itmp[1]
    if opt in ("-t", "--target_weight"):target_weight = float(arg)

p.prInfo(f"INPUT: [{input_dir}]")
p.prInfo(f"OUTPUT: [{output_dir}]")
p.prInfo(f"IMG 1: [{image_01}]")
p.prInfo(f"IMG 2: [{image_02}]")

if image_01 == False or image_02 == False:
    p.prErr("Missing one or both image names")
if output_dir == False or input_dir == False:
    p.prErr("Missing one or both in/output dirs")


#! output from the START command
hideSTDOUT = "2>&1 >> /tmp/START.log"

p.prInfo("Restarting Server")
p.prunlive("GPUMEMCLEAR")
if output_dir != False:
    cmd = f"~/src/longanim/START -i {input_dir} -o {output_dir} {hideSTDOUT} &"
else:
    p.cleandir(output_dir)
    cmd = f"./START {hideSTDOUT} &"

p.prCmd(cmd)
os.system(cmd)
p.wait_for_server()

with open("masks_v0_API.json") as f:
    prompt = json.load(f)

found = p.find_in_json(prompt,"weight")
for f in found: print(f)
found = p.find_in_json(prompt,"image")
for f in found: print(f)
found = p.find_in_json(prompt,"weight_type")
for f in found: print(f)
found = p.find_in_json(prompt,"width")
for f in found: print(f)
found = p.find_in_json(prompt,"height")
for f in found: print(f)

i1 = 0.0
i2 = 1.0
c = 0

curve = [0,0.03,0.06,0.09,0.12,0.15,0.18,0.21,0.23,0.25,0.27,0.29,0.31,0.33,0.35,0.37,0.39,0.41,0.42,0.43,0.44,0.45,0.46,0.47,0.48,0.49,0.5,0.51,0.52,0.53,0.54,0.55,0.56,0.57,0.58,0.59,0.6,0.62,0.64,0.66,0.68,0.7,0.72,0.74,0.76,0.78,0.81,0.84,0.87,0.9,0.93,0.96,0.99,1]

#for i in frange(0,1.01,0.01):
for j in curve:
    i = j*target_weight
    c = c + 1
    ni1 = round(i1+i,2)
    ni2 = round(i2-ni1,2)
    prefix = f"{c:04d}_{ni1:3.02f}-{ni2:3.02f}"
    print(f"=> {c:04d}_{prefix}")


    prompt['50']['inputs']['weight'] = ni1
    prompt['51']['inputs']['weight'] = ni2
    prompt['12']['inputs']['image'] = image_01 #from image (#1)
    prompt['27']['inputs']['image'] = image_02 # to image (#2)
    # prompt['50']['inputs']['weight_type'] = "linear"
    # prompt['51']['inputs']['weight_type'] = "linear"
    prompt['50']['inputs']['weight_type'] = "channel penalty"
    prompt['51']['inputs']['weight_type'] = "channel penalty"
    # prompt['4']['inputs']['text'] = prompt_01
    # prompt['6']['inputs']['text'] = ""

    prompt['59']["inputs"]["filename_prefix"] = prefix

    prompt['3']["inputs"]["width"] = width
    prompt['3']["inputs"]["height"] = height

    #! submit prompt
    prompt_id = p.queue_prompt(prompt)['prompt_id']

