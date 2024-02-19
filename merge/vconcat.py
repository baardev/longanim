#!/bin/env python
import os,sys
from glob import glob
import long_anim_lib as p

pwd = os.getcwd()

spec = sys.argv[1]

files = p.get_sorted_files(spec)

if len(files)>0:
    f = open("list","w")
    for file in files:
        print(f"Adding [{pwd}/{file}]",file=sys.stderr)
        f.write(f"file '{pwd}/{file}'\n")
    f.close
else:
    print(f"No files found", file=sys.stderr)
    exit()

cmd = f"ffmpeg -y -loglevel warning -f concat -safe 0 -i {pwd}/list -c copy {pwd}/concat.mp4"
print(cmd)

# p.prunlive(cmd)
# p.prInfo(f"OUTPUT: [{pwd}/concat.mp4]")

