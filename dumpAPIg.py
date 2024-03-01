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

def getNamebyId(id, ary):
    for e in WF_data['nodes']:
        # print(e['id'],"\n")
        if int(e['id']) == int(id):
            return e['type']

def showhelp():
    str = f"""
-h, --help     this test
-f, --file <path to json file>
"""
    print(str)
    exit()

input_filename = "/home/jw/store/src/longanim/merge/qmasks_v0.json"

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

#! workflow exists

p.prInfo(f"Workfile: [{WF_filename}]")
p.prInfo(f"API file: [{API_filename}]")


WFary = {}
if os.path.isfile(API_filename):
    with open(API_filename,"r") as f:
        rd = f.read()
    API_data = json.loads(rd)

    if os.path.isfile(WF_filename):
        print("XXXXXX")
        with open(WF_filename,"r") as f:
            rd = f.read()
        WF_data = json.loads(rd)
        for d in API_data:
            WFary[d]= getNamebyId(d,WF_data)
        # pprint(WFary)
    else:
        # for d in API_data:
        #     lev1 = Fore.LIGHTYELLOW_EX+f"['{d}']"+Fore.RESET
        #     print(f"'{d}':'',")

        for d in API_data:
            lev1 = Fore.LIGHTYELLOW_EX+f"['{d}']"+Fore.RESET
            try:
                print(f"'{d}':{Fore.LIGHTRED_EX}'{names[d]}',{Fore.RESET}")
                for e in API_data[d]['inputs']:
                    lev2 = f"['inputs']"+ Fore.LIGHTCYAN_EX + f"['{e}'] "+Fore.LIGHTBLUE_EX+" [{type(e)}]" + Fore.RESET
                    lev2val = API_data[d]['inputs'][e]
                    pre = f"{lev1}{lev2}"
                    print(f"\t[{lev1}]]{pre:70s} = {lev2val}")
            except:
                print(f"Add [{d}] to 'names' ")
    #! for just teh keys
#     for d in data:
#         lev1 = Fore.LIGHTYELLOW_EX+f"['{d}']"+Fore.RESET
#         print(f"'{d}':'',")
#
    for d in API_data:
        lev1 = Fore.LIGHTYELLOW_EX+f"['{d}']"+Fore.RESET
        # print(f"'{d}':{Fore.LIGHTRED_EX}'{WFary[d]}',{Fore.RESET}")
        print("")
        for e in API_data[d]['inputs']:
            lev2 = f"['inputs']"+ Fore.LIGHTCYAN_EX + f"['{e}']" + Fore.RESET
            lev2val = API_data[d]['inputs'][e]
            pre = f"{lev1}{lev2}"
            print(f"{Fore.LIGHTRED_EX}'{WFary[d]}',{Fore.RESET}] {pre:70s} = {str(lev2val):20s}"+Fore.LIGHTBLUE_EX+f" [{type(lev2val)}]")
            # print(f"\t[{lev1}] {pre:70s} = {str(lev2val):20s}"+Fore.LIGHTBLUE_EX+f" [{type(lev2val)}]")

# else:
#
#     for e in API_data['nodes']:
#         print(e['id'],"\n")
