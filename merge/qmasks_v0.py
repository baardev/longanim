#!/bin/env python
import json
import long_anim_lib as p
from pathlib import Path
from itertools import count, takewhile
import os
import sys
import getopt
from pprint import pprint
from colorama import init, Fore
init()
def frange(start, stop, step):
    tnary = []
    nary = takewhile(lambda x: x < stop, count(start, step))
    for i in list(nary):
        tnary.append(round(i,2))
    # print(tnary)
    return tnary
def setval(prompt,idx,key,val):
    p.prInfo(f"\t['{idx}']['inputs']['{key}'] = {val}")
    try:
        prompt[idx]['inputs'][key] = val
    except Exception as e:
        print(Fore.GREEN)
        pprint(sys.argv)
        print(Fore.RESET)

        print(Fore.RED)
        print(json.dumps(prompt,indent=4))
        print(Fore.RESET)

        print(Fore.YELLOW)
        print(f"ERROR: [{e}")
        print(f"SETTING:  |{key}| => |{val}|")
        print(f"TYPE: {type(e).__name__}")
        print("Existing keyvals:")
        showval(prompt,key)
        print(Fore.RESET)

        exit()


#!==================================================================================
p.prAnn("┌─────────────────────────────────────────────")
p.prAnn("│ ENTERED 'qmasks_v0.py'")
p.prAnn("└─────────────────────────────────────────────")

argv = sys.argv[1:]
opts = False
image_01 = False
image_02 = False
curve = "test"
try:
    opts, args = getopt.getopt(
        argv, "ho:i:p:r:t:c:",
        [   'help',
                    'output_dir=',
                    'input_dir=',
                    'images=',
                    'res=',
                    'target_weight=',
                    'curve=',
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
    if opt in ("-c", "--curve"):curve = arg

p.prInfo(f"INPUT: [{input_dir}]")
p.prInfo(f"OUTPUT: [{output_dir}]")
p.prInfo(f"IMG 1: [{image_01}]")
p.prInfo(f"IMG 2: [{image_02}]")
p.prInfo(f"CURVE: [{curve}]")

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

def showval(prompt,key):
    found = p.find_in_json(prompt, key)
    for f in found:
        p.prInfo("\t" + f)

p.prAnn("CURRENT VALUES:")
showval(prompt,"weight")
showval(prompt,"image")
showval(prompt,"weight_type")
showval(prompt,"width")
showval(prompt,"height")

i1 = 0.0
i2 = 1.0
c = 0

curves = {
    'test': [0,0.25,0.50,0.75,1],
    'optimal': [0,0.03,0.06,0.09,0.12,0.15,0.18,0.21,0.23,0.25,0.27,0.29,0.31,0.33,0.35,0.37,0.39,0.41,0.42,0.43,0.44,0.45,0.46,0.47,0.48,0.49,0.5,0.51,0.52,0.53,0.54,0.55,0.56,0.57,0.58,0.59,0.6,0.62,0.64,0.66,0.68,0.7,0.72,0.74,0.76,0.78,0.81,0.84,0.87,0.9,0.93,0.96,0.99,1],
    'linear': [],
}
for i in frange(0,1.01,0.01): curves['linear'].append(i)

#! NOTE: is the last file is not  named "*_1.00-0.00_00001_.png" then tehg 'waitinf_for_glob.py" will not work and must be changed

cnames = {
    'Empty_Latent_Image':'3',
    'Load_Image_1':'12',
    'Load_Image_2':'27',
    'Apply_IPAdapter_2':'50',
    'Apply_IPAdapter_1':'51',
    'Save_Image':'59',
}


applied_curve = curves[curve]

for j in applied_curve:
    i = j*target_weight
    c = c + 1
    ni1 = round(i1+i,2)
    ni2 = round(i2-ni1,2)
    prefix = f"{c:04d}_{ni1:3.02f}-{ni2:3.02f}"
    p.prInfo(f"PREFIX FILENAME => |{c:04d}_{prefix}|")


    p.prAnn("UPDATED VALUES:")

    setval(prompt,cnames['Empty_Latent_Image'],"width",width) #3
    setval(prompt,cnames['Empty_Latent_Image'],"width",height) # 3

    setval(prompt,cnames['Load_Image_1'],"image",f"{image_01}") # 12

    setval(prompt,cnames['Load_Image_2'],"image",f"{image_02}") # 27

    setval(prompt,cnames['Apply_IPAdapter_2'],"weight",str(ni1)) # 50

    setval(prompt,cnames['Apply_IPAdapter_1'],"weight",str(ni2)) # 51

    setval(prompt,cnames['Save_Image'],"filename_prefix",prefix) # 59


    #! submit prompt
    prompt_id = p.queue_prompt(prompt)['prompt_id']

p.prInfo("┌─────────────────────────────────────────────")
p.prInfo("│ EXITING 'qmasks_v0.py'")
p.prInfo("└─────────────────────────────────────────────")
