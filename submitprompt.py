#!/bin/env python
import json
import long_anim_lib as p
from pathlib import Path
from itertools import count, takewhile
import os
import sys
import getopt
from pprint import pprint
import toml
from colorama import init, Fore
import time
from sklearn.preprocessing import minmax_scale
#! ex:  xdata = minmax_scale(data, feature_range=(0, 10), axis=0, copy=True)

def showval(prompt,key):
    found = p.find_in_json(prompt, key)
    for f in found:
        p.prInfo("\t" + f)
def setval(prompt,idx,key,val,**kwargs):
    verbose = p.tryit(kwargs,"verbose",False)

    p.prInfo(f"\t['{idx}']['inputs']['{key}'] = {val} ({type(val)})")
    try:
        prompt[idx]['inputs'][key] = val
        return prompt
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

with open("/home/jw/store/src/longanim/PROJECTS/boat/video_test_API.json") as f:
    prompt = json.load(f)

setvalVerbose = True

#set defaults
#! IPAdapterApply
# prompt = setval(prompt,"37","noise",0.0,verbose = setvalVerbose)  # 80
# prompt = setval(prompt,"37","weight",0.66,verbose = setvalVerbose)  # 80




RUN = True
# RUN = False
# ! loop IPAdaptor_Plus start/etc values
# ^ █████████████████████████████████████████████████████████████████████████
def IPAdaptor_Plus(RUN):
    global count
    count = 0
    startat = [0.0,0.2,0.4,0.6,0.8,1.0,  0.0,1.0,  0.0,0.2,0.4,0.6,0.8]
    endat =   [1.0,1.0,1.0,1.0,1.0,1.0,  0.0,1.0,  0.2,0.4,0.6,0.8,1.0]
    for i in range(len(startat)):
        st = startat[i]
        en = endat[i]
        prefix = f"StartAt={st}_EndAt={en}"
        prompt = setval(prompt,"37","start_at",st,verbose = setvalVerbose)  # 80
        prompt = setval(prompt,"37","end_at",en,verbose = setvalVerbose)  # 80
        prompt = setval(prompt,"207","filename_prefix",prefix,verbose = setvalVerbose)  # 80

        if RUN == True:
            p.save_prompt(prompt,location = f"/tmp/prompt_{prefix}.json")
            prompt_id = p.queue_prompt(prompt)['prompt_id']

        count = count + 1

# ! loop Motion Loras
# ^ █████████████████████████████████████████████████████████████████████████
def motion_loras(RUN):
    global count
    loras=[
    "v2_lora_PanLeft.ckpt",
    "v2_lora_PanRight.ckpt",
    "v2_lora_RollingAnticlockwise.ckpt",
    "v2_lora_RollingClockwise.ckpt",
    "v2_lora_TiltDown.ckpt",
    "v2_lora_TiltUp.ckpt",
    "v2_lora_ZoomIn.ckpt",
    "v2_lora_ZoomOut.ckpt",
    ]
    # strength = ["0","1","2"]
    strength = ["2"]
    for loraname in loras:
        for str in strength:
            prefix = f"{loraname}_{str}x"
            prompt = setval(prompt,"66","lora_name",loraname,verbose = setvalVerbose)  # 80
            prompt = setval(prompt,"66","strength",float(str),verbose = setvalVerbose)  # 80
            prompt = setval(prompt,"207","filename_prefix",prefix,verbose = setvalVerbose)  # 80
            count = count + 1

            if RUN == True:
                prompt_id = p.queue_prompt(prompt)['prompt_id']

# ! loop IPAdaptor_Plus start/etc values
# ^ █████████████████████████████████████████████████████████████████████████

def cfgs(prompt,RUN):
    global count
    cfgs1 = [3,5,7]
    cfgs2 = [7,5,3]

    for i in range(len(cfgs1)):
        for j in range(len(cfgs1)):
            cfg1 = cfgs1[i]
            cfg2 = cfgs2[j]
            print(f"{cfg1} {cfg2}")
            prefix = f"KS1cfg={cfg1}_KS2cfg={cfg2}"
            prompt = setval(prompt, "234", "cfg", cfg1, verbose=setvalVerbose)  # 80
            prompt = setval(prompt, "233", "cfg", cfg2, verbose=setvalVerbose)  # 80
            prompt = setval(prompt, "207", "filename_prefix", prefix, verbose=setvalVerbose)  # 80

            if RUN == True:
                p.save_prompt(prompt, location=f"/tmp/prompt_{prefix}.json")
                prompt_id = p.queue_prompt(prompt)['prompt_id']

            count = count + 1


file = False
execute = False
argv = sys.argv[1:]
try:
    opts, args = getopt.getopt(
        argv, "hf:x",
        [   'help',
                    'file=',
                    'execute=',
                ],
    )
except Exception as e:
    print(str(e))

for opt, arg in opts:
    # if opt in ("-h", "--help"):p.showhelp()
    if opt in ("-f", "--file"):file = arg
    if opt in ("-x", "--execute"):execute = True



with open("/home/jw/store/src/longanim/PROJECTS/boat/video_test_API.json") as f:
    prompt = json.load(f)

count = 0
# IPAdaptor_Plus(RUN)
# motion_loras(RUN)
cfgs(prompt,execute)

print(f"Count:   [{count}]")
print(f"Minutes: [{count*15}]")
print(f"Hours:   [{(count*15)/60}]")

