#!/bin/python

import json
import getopt
import os
# import proclib as p
from pprint import pprint
import getopt
import glob
from colorama import init, Fore
import sys
from tempfile import mktemp

# sys.path.append("/home/jw/src/sdc/settings/preprocs")
# import preprocessors as pre
import contextlib

init()


def showhelp():
    print("help")
    rs = f"""
    -h, --help          Help  
    -m, --mode          "6x1","6x3","8x4"
    -o, --output        save output to filename
    -s, --skipconfirm   'Y' to deletion of existing videos
    -D, --dirnames       use dir names a labels
"""
    print(rs)
    exit()


basedir = os.getcwd()#"/home/jw/src/ComfyUI/output/mp4"

# project_name = os.getcwd().split("/")[-1]
project_name = ""
mode = "6x1"
Xg = 6
Yg = 1
gs = Xg * Yg
output_fn = "RUN"
confirm = True
dirnames = False
debug=True
argv = sys.argv[1:]
try:
    opts, args = getopt.getopt(
        argv,
        "hm:so:D",
        [
            "help",
            "mode=",
            "skipconfirm",
            "output=",
            "dirnames",
        ],
    )
except Exception as e:
    print(str(e))

for opt, arg in opts:
    if opt in ("-h", "--help"):
        showhelp()
    if opt in ("-m", "--mode"):
        mode = arg
        Xg = int(arg.split("x")[0])
        Yg = int(arg.split("x")[1])
        gs = Xg * Yg
    if opt in ("-s", "--skipconfirm"):
        confirm = False
    if opt in ("-o", "--output"):
        output_fn = arg
    if opt in ("-D", "--dirnames"):
        dirnames = True

print(Fore.CYAN + f"basedir:" + Fore.WHITE + basedir + Fore.RESET, file=sys.stderr)
print(Fore.CYAN + f"name:" + Fore.WHITE + project_name + Fore.RESET, file=sys.stderr)
print(Fore.CYAN + f"mode:" + Fore.WHITE + mode + Fore.RESET, file=sys.stderr)


# [ SET DIRECTORIES
os.chdir(basedir)


# [ load json of base settings
# settings_fn = "BASE_SETTINGS.json"
# settings_fp = open(settings_fn, "r")
# settings_dict = json.load(settings_fp)

# prp_list = [line.rstrip() for line in open(prp_list_fn)]

ptmp = []
for f in glob.glob("./**/*.mp4",recursive=True):
    print(f.split(("/"))[1])
    # if os.path.isdir(f):
    ptmp.append(f.split(("/"))[1])
prp_cleaned = ptmp

# print(prp_cleaned)
# exit()

# print(gs)
# pprint(prp_cleaned)
# exit()

fontsize = 20
b_list = []
l_list = []


pprint(prp_cleaned)
for prp in prp_cleaned:
    tmpfile = f"{mktemp()}.mp4"
    color = "black"
    prpt = str(prp).replace("_00001_.mp4","")
    prpt = str(prp).replace(".mp4","")

    label = f'magick -background darkgray -fill black -pointsize 25 -gravity center  -font Carlito-Regular -size 512x25  label:"{prpt}"   /tmp/label.png; \n'
    label += f'ffmpeg  -y -loglevel warning -i ./{prp} -i /tmp/label.png -filter_complex "[0:v][1:v] overlay=0:0" -pix_fmt yuv420p -c:a copy {tmpfile}; \n'
    label += f"mv {tmpfile} {prp}; \n"
    label += f'echo "----[LABEL] {prp}-------------------------------------"\n'

    border = f"ffmpeg -y -loglevel warning -i {prp} -vf drawbox=x=0:y=0:w=in_w:h=512:color={color} {tmpfile}; mv {tmpfile} {prp}\n"
    border += f'echo "----[BORDER] {prp} -------------------------------------"\n'

    l_list.append(label)
    b_list.append(border)

output_fh = open(output_fn, "w")
for l in l_list:
    output_fh.write(l)
    output_fh.write("\n")
for b in b_list:
    output_fh.write(b)

output_fh.close()
