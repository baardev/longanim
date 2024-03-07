#!/bin/env python
import long_anim_lib as p
import os
import sys
import getopt
from glob import glob
from pprint import pprint
import ffmpeg

def xos(cmd):
    # print(cmd)
    os.system(cmd)
def sos(cmd):
    # print(cmd)
    p.prunlive(cmd)

def get_rate(filename):
    print(filename,flush=True)
    probe = ffmpeg.probe(filename)
    video_streams = [stream for stream in probe["streams"] if stream["codec_type"] == "video"]
    fpsratio = video_streams[0]['avg_frame_rate']
    p = str(fpsratio).split("/")
    fps = p[0]
    return fps
def get_duration(filename):
    print(filename,flush=True)
    probe = ffmpeg.probe(filename)
    video_streams = [stream for stream in probe["streams"] if stream["codec_type"] == "video"]
    dur = video_streams[0]['duration']
    return float(dur)


# !==================================================================================
argv = sys.argv[1:]
opts = False
frame_rate = 8
interpsecs = 1
interpolate = interpsecs*frame_rate
output_file = "iout.mp4"
algo = "xfade" # or "interp"

name = "unnamed"
try:
    opts, args = getopt.getopt(
        argv, "hv:o:I:F:a:",
        ['help',
         'videos',
         'outfile',
         'interpsecs',
         'rate',
         'algo'
         ],
    )
except Exception as e:
    print(str(e))

videos = False
vid1 = False
vid2 = False
vparts = []


for opt, arg in opts:
    # if opt in ("-h", "--help"): p.showhelp()
    if opt in ("-o", "--outfile"): output_file = arg
    if opt in ("-v", "--videos"):
        vparts = str(arg).split(":")
        vid1 = f"{os.getcwd()}/{vparts[0]}"
        vid2 = f"{os.getcwd()}/{vparts[1]}"
        vparts = [vid1,vid2]
        # frame_rate = get_rate(vid1)
    #! this has to coma eAFTEr ffmpeg.probe
    if opt in ("-F", "--frame_rate"): frame_rate = int(arg)
    if opt in ("-I", "--interpsecs"):
        interpsecs = int(arg)
        interpolate = interpsecs * frame_rate

if algo == "interp":

    # ! extract vids
    dirs = ['/tmp/vid1','/tmp/vid3']
    print(vparts)
    for i in range(len(vparts)):
        if os.path.isdir(dirs[i]):
            cmd = f"rm -rf {dirs[i]}"
            print(cmd)
            p.prunlive(cmd)
        xos(f"mkdir {dirs[i]}")
        sos(f"ffmpeg -y -loglevel warning -i {vparts[i]} -r {frame_rate}/1 {dirs[i]}/%09d.png")

    if os.path.isdir("/tmp/vid2"):
        sos(f"rm -rf /tmp/vid2")
    sos(f"mkdir /tmp/vid2")
    #! copy last image
    files = glob("/tmp/vid1/*png")
    xos(f"cp {files[-1]} /tmp/vid2/xx1.png")
    #! copy first image
    files = glob("/tmp/vid3/*png")
    xos(f"cp {files[0]} /tmp/vid2/xx3.png")
    sos(f"./simple_interp_images.sh /tmp/vid2 {interpolate} /tmp/vid2")
    sos("rm /tmp/vid2/xx1.png")
    sos("rm /tmp/vid2/xx3.png")

    v1files = p.get_sorted_files("/tmp/vid1/*.png")
    v2files = p.get_sorted_files("/tmp/vid2/*.png")
    v3files = p.get_sorted_files("/tmp/vid3/*.png")

    if os.path.isdir("/tmp/vid123"):
        xos(f"rm -rf /tmp/vid123")
        xos("mkdir /tmp/vid123")
    j=1
    for i in range(len(v1files)):
        k = f"{j:06d}"
        xos(f"cp {v1files[i]} /tmp/vid123/{k}.png")
        j += 1
    for i in range(len(v2files)):
        k = f"{j:06d}"
        xos(f"cp {v2files[i]} /tmp/vid123/{k}.png")
        j += 1
    for i in range(len(v3files)):
        k = f"{j:06d}"
        xos(f"cp {v3files[i]} /tmp/vid123/{k}.png")
        j += 1

    sos(f"ffmpeg -y -loglevel warning -framerate {frame_rate} -pattern_type glob -i /tmp/vid123/*.png  -c:v libx264 -pix_fmt yuv420p {output_file}")
    print (f"SAVED: {output_file}")

if algo == "xfade":

    dur = get_duration(vid1)
    # print(dur)
    sos(f"ffmpeg -y -loglevel warning -i {vid1} -i {vid2} -filter_complex xfade=transition=circleopen:duration={interpsecs}:offset={dur-interpsecs} {output_file}")

"""
to interoplate and join 10 files...
F=60
./interpolate_util.py -I 60 -F ${F} -v ASSETS/KEEP/01.mp4:ASSETS/KEEP/02.mp4 -o x1.mp4
./interpolate_util.py -I 60 -F ${F} -v ASSETS/KEEP/03.mp4:ASSETS/KEEP/04.mp4 -o x2.mp4
./interpolate_util.py -I 60 -F ${F} -v ASSETS/KEEP/05.mp4:ASSETS/KEEP/06.mp4 -o x3.mp4
./interpolate_util.py -I 60 -F ${F} -v ASSETS/KEEP/07.mp4:ASSETS/KEEP/08.mp4 -o x4.mp4
./interpolate_util.py -I 60 -F ${F} -v ASSETS/KEEP/09.mp4:ASSETS/KEEP/10.mp4 -o x5.mp4
./interpolate_util.py -I 60 -F ${F} -v x1.mp4:x2.mp4 -o y1.mp4
./interpolate_util.py -I 60 -F ${F} -v x3.mp4:x4.mp4 -o y2.mp4
./interpolate_util.py -I 60 -F ${F} -v y1.mp4:y2.mp4 -o z1.mp4
./interpolate_util.py -I 60 -F ${F} -v z1.mp4:x5.mp4 -o interpolated_file.mp4


to xfade 6 files...
F=24
./interpolate_util.py -a xfade -I 1 -F ${F} -v ASSETS/KEEP/01.mp4:ASSETS/KEEP/02.mp4 -o ix1.mp4
./interpolate_util.py -a xfade -I 1 -F ${F} -v ASSETS/KEEP/03.mp4:ASSETS/KEEP/04.mp4 -o ix2.mp4
./interpolate_util.py -a xfade -I 1 -F ${F} -v ASSETS/KEEP/05.mp4:ASSETS/KEEP/06.mp4 -o ix3.mp4
./interpolate_util.py -a xfade -I 1 -F ${F} -v ix1.mp4:ix2.mp4 -o iy1.mp4
./interpolate_util.py -a xfade -I 1 -F ${F} -v iy1.mp4:ix3.mp4 -o xfaded_file.mp4




"""