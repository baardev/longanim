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
argv = sys.argv[1:]
try:
    opts, args = getopt.getopt(
        argv, "hf:t:",
        [   'help',
            'file=',
            'type=',

            ],
    )
except Exception as e:
    print(str(e))


def getNamebyId(id, ary):
    for e in WF_data['nodes']:
        # print(e['id'],"\n")
        if int(e['id']) == int(id):
            return e['type']


input_filename = "/home/jw/store/src/longanim/merge/qmasks_v0.json"

for opt, arg in opts:
    if opt in ("-h", "--help"):p.showhelp()
    if opt in ("-f", "--file"):input_filename = arg

parts = p.split_path(input_filename)
if input_filename.find("API") != -1 :
    #! this is an API file
    API_filename = input_filename
    x = parts['nameonly'].replace("_API","")
    WF_filename = f"{parts['dirname']}/{x}.json"
else:
    WF_filename = input_filename
    API_filename = f"{parts['dirname']}/{parts['nameonly']}_API.json"

names = {
    '1': 'KSampler',
    '2': 'Load Checkpoint',
    '3': 'Empry Latent Image',
    '4': 'CLIP Text Encode (pos)',
    '5': 'CLIP Text Encode (neg)',
    '6': 'VAE Decode',
    '10': 'Load IPAdapter Model',
    '11': 'Load Clip Vision',
    '12': 'Load Image (1)',
    '13': 'Prepare Image for Clip Vision',
    '27': 'Load Image (2)',
    '50': 'Apply IPAdapter (2)',
    '51': 'Apply IPAdapter (1)',
    '52': 'Prepare Image for Clip Vision',
    '59': 'Save Image',
    '64': 'Load Images (upload)',
    '66': 'Apply Controlnet (Advanced)',
    '67': 'Load Advanced ControlNet Model',
    '74': 'AnimateDiff Loader (Legacy)',
    '75': 'Context Options Looped Uniform',
    '76': 'ksampler_2',
    '80': 'Load image as mask',
    '81': 'Ksampler Adv. Efficient',
    '83': 'Highres Fix Script',
}

#! workflow exists

p.prInfo(f"Workfile: [{WF_filename}]")
p.prInfo(f"API file: [{API_filename}]")

if os.path.isfile(API_filename):
    with open(API_filename,"r") as f:
        rd = f.read()
    API_data = json.loads(rd)

    if os.path.isfile(WF_filename):
        with open(input_filename,"r") as f:
            rd = f.read()
        WF_data = json.loads(rd)
        for d in API_data:
            print(f"\'{d}_{getNamebyId(d,WF_data)}\': '{d}',")
    else:
        # for d in API_data:
        #     lev1 = Fore.LIGHTYELLOW_EX+f"['{d}']"+Fore.RESET
        #     print(f"'{d}':'',")

        for d in API_data:
            lev1 = Fore.LIGHTYELLOW_EX+f"['{d}']"+Fore.RESET
            try:
                print(f"'{d}':{Fore.LIGHTRED_EX}'{names[d]}',{Fore.RESET}")
                for e in API_data[d]['inputs']:
                    lev2 = f"['inputs']"+ Fore.LIGHTCYAN_EX + f"['{e}']" + Fore.RESET
                    lev2val = API_data[d]['inputs'][e]
                    pre = f"{lev1}{lev2}"
                    print(f"\t{pre:70s} = {lev2val}")
            except:
                print(f"Add [{d}] to 'names' ")
    #! for just teh keys
#     for d in data:
#         lev1 = Fore.LIGHTYELLOW_EX+f"['{d}']"+Fore.RESET
#         print(f"'{d}':'',")
#
    for d in API_data:
        lev1 = Fore.LIGHTYELLOW_EX+f"['{d}']"+Fore.RESET
        try:
            print(f"'{d}':{Fore.LIGHTRED_EX}'{names[d]}',{Fore.RESET}")
            for e in API_data[d]['inputs']:
                lev2 = f"['inputs']"+ Fore.LIGHTCYAN_EX + f"['{e}']" + Fore.RESET
                lev2val = API_data[d]['inputs'][e]
                pre = f"{lev1}{lev2}"
                print(f"\t{pre:70s} = {lev2val}")
        except:
            print(f"Add [{d}] to 'names' ")

# else:
#
#     for e in API_data['nodes']:
#         print(e['id'],"\n")
