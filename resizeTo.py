#!/home/jw/miniconda3/bin/python

import sys
import getopt
from colorama import init, Fore, Back
from pprint import pprint
import long_anim_lib as p

def showhelp():
    print("help")
    rs = """
    -h, --help          show help
    -f, --filename      full or partial filename Ex: /tmp/*.mp4"
    -d, --dims          x:y
"""
    print(rs)
    exit()

dims = False
H=False
W=False
filename = False

# for testing
# dims = "486x864"
# H=486
# W=864
# filename = "/home/jw/src/longanim/PROJECTS/aniani/output/input/xxx.png"

# v ────────────────────────────────────────────────────────────────────────────────────────────────────────────
argv = sys.argv[1:]
try:
    opts, args = getopt.getopt(
        argv,
        "hf:d:",
        [
            "help",
            "filename=",
            "dims=",
        ],
    )
except Exception as e:
    print(str(e))

for opt, arg in opts:
    if opt in ("-h", "--help"): showhelp()
    if opt in ("-f", "--filename"): filename = arg
    if opt in ("-d", "--dims"):
        dims=arg
        W=int(dims.split(":")[0])
        H=int(dims.split(":")[1])

parts = p.split_path(filename)

#!/bin/bash

#! double in size
cmd = f"/home/jw/src/longanim/simple_upscale_image.sh {filename} 2 /tmp/"
p.prCmd(cmd)
p.prunlive(cmd,debug=True)


p.prCmd(cmd)
cmd = f"convert /tmp/{parts['nameonly']}_out.{parts['ext']} -resize -1:{H} /tmp/rsx.png"
p.prCmd(cmd)
p.prunlive(cmd,debug=True)

cmd = f"convert /tmp/rsx.png -gravity Center -trim -extent {W}x{H} {parts['nameonly']}_{W}x{H}.{parts['ext']}"
p.prCmd(cmd)
p.prunlive(cmd,debug=True)

print(f"New File: {filename}")

