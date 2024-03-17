#!/bin/env python
from os import fsencode
from pyexif import pyexif
import exiftool
import sys
import getopt
import json
from pprint import pprint
from pyexiv2 import Image
from colorama import Fore
import chardet
import long_anim_lib as p


def getdata(file, retrieve):
    et = exiftool.ExifToolHelper()
    exif_dict = et.get_metadata(file)
    # print(exif_dict)
    edata = exif_dict[0]
    elen = len(edata)
    print(elen, type(edata))
    for key in edata:
        if key != "PNG:Prompt" and key != 'PNG:Workflow':
            print(f"{Fore.YELLOW}{key}{Fore.RESET} {Fore.CYAN}{edata[key]}{Fore.RESET}")

    for key in edata:
        # ! PNG:Prompt = API
        # ! PNG:Workflow = editable
        if key == "PNG:Prompt" and retrieve == "prompt":
            api_obj = json.loads(edata[key])
            fstr = json.dumps(api_obj, indent=4)
            # print(fstr)
            return fstr

        if key == "PNG:Workflow" and retrieve == "workflow":
            api_obj = json.loads(edata[key])
            fstr = json.dumps(api_obj, indent=4)
            # print(fstr)
            return fstr


argv = sys.argv[1:]
opts = False
retrieve = "prompt"
diff = False
file = "/home/jw/src/longanim/PROJECTS/waterboy/output_512/safe/hy/VFI_hy___00006.png"
diff = "/home/jw/src/longanim/PROJECTS/waterboy/output_512/safe/hy2/VFI_hy2___00006.png"

try:
    opts, args = getopt.getopt(
        argv, "hr:f:d:",
        ['help',
         'retrieve=',
         'file=',
         'diff=',
         ],
    )
except Exception as e:
    print("ERROR:",str(e))

for opt, arg in opts:
    # if opt in ("-h", "--help"): p.showhelp()
    if opt in ("-f", "--file"): file = arg
    if opt in ("-r", "--retrieve"): retrieve = arg
    if opt in ("-d", "--diff"): diff = arg


f1str = getdata(file,retrieve)
with open("/tmp/fnum_1_API.json","w") as f:  f.write(getdata(file,"prompt"))
with open("/tmp/fnum_1.json","w") as f:  f.write(getdata(file,"workflow"))

if diff != False:
    f2str = getdata(diff, retrieve)
    with open("/tmp/fnum_2_API.json", "w") as f: f.write(getdata(diff, "prompt"))
    with open("/tmp/fnum_2.json", "w") as f: f.write(getdata(diff, "workflow"))

    cmd = f"diff /tmp/fnum_1_API.json /tmp/fnum_2_API.json"
    p.prunlive(cmd)
else:
    print(f1str)
