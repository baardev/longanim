#!/bin/env python


import os
import sys
from glob import glob
from pprint import pprint
import getopt
import time
import long_anim_lib as p

def showhelp():
    str = f"""
-h, --help     this test
-g, --grid   <grid size>  ex: 3x3
-o, --output <name of output file>
"""
    print(str)
    exit()

argv = sys.argv[1:]
try:
    opts, args = getopt.getopt(argv, "hg:o:",['help','grid=','output='])
except Exception as e:
    print(str(e))

outputfile = False
grid = False

for opt, arg in opts:
    if opt in ("-h", "--help"):p.showhelp()
    if opt in ("-o", "--output"):outputfile = arg
    if opt in ("-g", "--grid"):grid = arg

if outputfile == False or grid == False:
    showhelp()

def process(cmd,**kwargs):
    how = p.tryit("how",kwargs,"os")
    p.prCmd(cmd)
    if how == "sub":
        p.prunlive(cmd)
    else:
        os.system(cmd)
#! get current dir
cwd = os.getcwd()
#! check for safe, rename if exists, them mk
if os.path.isdir(f"{cwd}/safe"):
    tt = int(time.time())
    p.prInfo(f"[{cwd}/safe] exists.. moving to [{cwd}/safe.{tt}]")
    process(f"mv {cwd}/safe {cwd}/safe.{tt}")
p.prInfo(f"making [{cwd}/safe]")
process(f"mkdir {cwd}/safe",how="os")
#! cope all mop4s to safe
process(f"cp *.mp4 safe",how="os")
#! cd to safe
os.chdir(f"{cwd}/safe")
#! frinm genlabels
process("/home/jw/src/longanim/genlabels2.py")
#! run RUN
process("sh ./RUN")
process("rm RUN",how="os")
#! run mergevidX
process(f"mergevidX.py --filename '*.mp4' --grid {grid} -d")

files = glob("out/*mp4")
process(f"mv {files[0]} out/{outputfile}.mp4",how="os")
