#!/bin/env python
import math
import os, sys, glob, getopt
from colorama import init, Fore, Back
from pprint import pprint
import proclib as p
import math as m
from tempfile import mktemp
from operator import itemgetter
import primefac

init()
# input("Make sure you are in the directory that holds the output directories of Deforum")


def showhelp():
    print("help")
    rs = """
    -h, --help          show help
    -f, --filename      full or partial filename Ex: /tmp/*.mp4"
    -D, --destdir       directory
    -d, --debug
    -g, --grid          XxY
    -t, --testvc        test video count
    -r, --rootdir       top dir of catagory
    -p, --project       project name      
"""
    print(rs)
    exit()


# [set default vals
# mode = "all"
# mode = "clean"
# if mode == "clean":
#     filename = "./[^Z_]*.mp4"

path = os.getcwd() + "/*.mp4"
root_dir = os.getcwd()  # "/home/jw/src/sdc/settings/preprocs"
project = os.getcwd().split("/")[-1]  #! use folder name


verbose = False
ffmpeg_verbose = "-loglevel error"
testvc = False
Xr = 512
Yr = 512
Xg = 1
Yg = 1
grid = "6x3"  # [default size for full screen. holds 18 images


# v ────────────────────────────────────────────────────────────────────────────────────────────────────────────
# [ get args
argv = sys.argv[1:]
try:
    opts, args = getopt.getopt(
        argv,
        "hf:D:dg:t:",
        [
            "help",
            "filename=",
            "destdir=",
            "debug",
            "grid=",
            "testvc=",
        ],
    )
except Exception as e:
    print(str(e))

for opt, arg in opts:
    if opt in ("-t", "--testvc"):
        testvc = int(arg)
    if opt in ("-h", "--help"):
        showhelp()
    if opt in ("-f", "--filename"):
        pathparts = p.split_path(arg)
        filepath = pathparts["dirname"]
        filename = pathparts["basename"]
    if opt in ("-D", "--destdir"):
        destdir = arg
    if opt in ("-d", "--debug"):
        verbose = True
        ffmpeg_verbose = "-loglevel warning"
    if opt in ("-g", "--grid"):
        parts = str(arg).split("x")
        grid = arg
        Xg = int(parts[0])
        Yg = int(parts[1])
        # print(f"grid => Xg/Yh:{Xg}/{Yg}")

pathparts = p.split_path(path)
filepath = pathparts["dirname"]
filename = pathparts["basename"]
project_dir = f"{root_dir}"
destdir = f"{project_dir}/out"


print(Fore.CYAN + f"filepath:" + Fore.WHITE + filepath + Fore.RESET)
print(Fore.CYAN + f"filename:" + Fore.WHITE + filename + Fore.RESET)
print(Fore.CYAN + f"destdir:" + Fore.WHITE + destdir + Fore.RESET)
print(Fore.CYAN + f"root_dir:" + Fore.WHITE + root_dir + Fore.RESET)
print(Fore.CYAN + f"project_dir:" + Fore.WHITE + project_dir + Fore.RESET)

# [make destdir if not exist
if not os.path.exists(destdir):
    os.mkdir(destdir)


# v ────────────────────────────────────────────────────────────────────────────────────────────────────────────


def ratios(totvids):
    factors = list(primefac.primefac(totvids))
    return factors


def cleanpre():
    for f in glob.glob("/tmp/tmp*vgrid*"):
        os.unlink(f)
    cleanpost()


def cleanpost():
    for f in glob.glob("/tmp/tmp*output*"):
        os.unlink(f)


def chunks(l, n):
    tary = [l[i : i + n] for i in range(0, len(l), n)]

    return tary


def merge_h(vids, Xg, Yg, count, all_grids):
    hcounts = []
    output_fn = f"{mktemp()}_output"

    for Y in range(Yg):
        print(f"{Y+1} of {Yg}")
        """
        We 'try' here because we assume any error is a index error because there were not enough elements to fill the array.
        By 'passing' the error, we force ffmpeg to fill in the empty spaces or eliminate empty rows
        """

        try:
            rowVids = vids[Y]
            print(
                Fore.GREEN
                + f"Merging {len(rowVids)} videos into row {Y+1}."
                + Fore.RESET
            )
            cmd = f"ffmpeg {ffmpeg_verbose} -y "
            for X in range(len(rowVids)):
                cmd += f" -i {rowVids[X]} "
            xtra = f' -fps_mode passthrough -filter_complex "[0]"pad=iw+5:color=black"[left]";"[left]""[1]"hstack=inputs={len(rowVids)} {output_fn}_{Y}.mp4'
            cmd += xtra
            hcounts.append(Y)
            p.prun(cmd, debug=verbose)
            # print(f">>>>>>>  {len(rowVids)} < {Xg}:")
            if len(rowVids) < Xg:
                # if len(vids[-1]) <= Xg:
                # cmd = f"ffmpeg {ffmpeg_verbose} -y -i {output_fn}_{Y}.mp4 -vf pad=2564:ih:color=black {output_fn}_i_{Y}.mp4"
                cmd = f"ffmpeg {ffmpeg_verbose} -y -i {output_fn}_{Y}.mp4 -vf pad=256:ih:color=black {output_fn}_i_{Y}.mp4"
                # cmd = f"ffmpeg {ffmpeg_verbose} -y -i {output_fn}_{Y}.mp4 -vf ih:color=black {output_fn}_i_{Y}.mp4"
                p.prun(cmd, debug=verbose)
                cmd=f"cp {output_fn}_i_{Y}.mp4 {output_fn}_{Y}.mp4 "
                p.prun(cmd, debug=verbose)


        except:
            pass
        # print(hcounts)
    # if len(vids[-1]) <= Xg and len(hcounts) > 1:
    if len(hcounts) == Yg:
        print(
            Fore.GREEN
            + f"Merging {len(hcounts)} rows to "
            + Fore.CYAN
            + f"{destdir}/vgrid-{grid}_{count+1}_of_{all_grids}.mp4"
            + Fore.RESET
            + "."
        )

        print(hcounts)
        if len(hcounts) == 1:
            cmd = f"cp {output_fn}_0.mp4 {destdir}/vgrid-{grid}_{count+1}_of_{all_grids}.mp4"
        else:
            cmd = f"ffmpeg -y -y {ffmpeg_verbose} "
            for h in hcounts:
                cmd += f" -i {output_fn}_{h}.mp4"

            # xtra   = f' -fps_mode passthrough -filter_complex color=c=black"[c_s]"; "[c_s]""[0:v]"scale2ref"[c]""[v]"; "[c]"setsar=1"[cr]"; "[v]""[cr]"vstack=shortest=1:inputs={len(hcounts)}"[combined]" -map "[combined]" {destdir}/vgrid-{grid}_{count+1}_of_{all_grids}.mp4'
            xtra = f' -fps_mode passthrough -filter_complex "[0:v]""[1:v]"vstack=inputs={len(hcounts)}:shortest=1"[outv]" -map "[outv]" {destdir}/vgrid-{grid}_{count+1}_of_{all_grids}.mp4'
            cmd += xtra
        p.prun(cmd, debug=verbose)

    else:
        print(
            Fore.GREEN
            + f"Merging remaining {len(vids[-1])} videos to "
            + Fore.CYAN
            + f"{destdir}/vgrid_{count+1}_of_{all_grids}.mp4"
            + Fore.RESET
            + "."
        )
        cmd = f"mv {output_fn}_{hcounts[-1]}.mp4 {destdir}/vgrid-{grid}_{count+1}_of_{all_grids}.mp4"
        p.prun(cmd, debug=verbose)


# v ────────────────────────────────────────────────────────────────────────────────────────────────────────────
# v ────────────────────────────────────────────────────────────────────────────────────────────────────────────

# cleanpre()
vgrid_fn = f"{mktemp()}_vgrid"  #! make temporary filename for vgrid outoput
#! get all files by spec
# vids = glob.glob(f"{project_dir}/{filename}")
vids = glob.glob(f"{filename}")
# pprint(vids)

vtmp = []
#! if a 'base' image exists, insert INPUT_VIDEO in to #1 position

# exit()
#! append all globbed videos to list
for v in vids:
    if (v != "INPUT_VIDEO.mp4") and (v != "ORG_VIDEO.mp4"):
        vtmp.append(v)
#! make and order vid list, sort and get count
vids = vtmp
vids.sort()
# pprint(vids)
if os.path.exists("none.mp4"):
    gs = Xg * Yg
    for i in range(0, len(vids) + (int(len(vids) / gs) + gs), gs):
        vids.insert(i, "none.mp4")
        # i += ((Xg*Yg)+1)
    # if vids[-1] == "INPUT_VIDEO.mp4":
    #     ,,vids.pop()
if os.path.exists("ORG_VIDEO.mp4"):
    gs = Xg * Yg
    for i in range(0, len(vids) + (int(len(vids) / gs) + gs), gs):
        vids.insert(i, "ORG_VIDEO.mp4")
        # i += ((Xg*Yg)+1)
    # if vids[-1] == "ORG_VIDEO.mp4":
    #     ,,vids.pop()

#! crop the array to the size of X*Y
vids = vids[:Xg*Yg]
# pprint(vids)
total_vids = len(vids)

print(f"FOUND: {len(vids)}")
print(f"Cur Grid: {total_vids} ", ratios(total_vids))

#! testvc is used to precals grid info
if testvc != False:
    print(f"Alt Grid: {testvc} ", ratios(testvc))
    exit()
#! calculate the number of images missing to completely fill the grid
missing = (Xg * Yg) - (len(vids) % (Xg * Yg))
#! calculate the number of images short of a full grid
remainder = int(((total_vids / (Xg * Yg)) - int(total_vids / (Xg * Yg))) * (Xg * Yg))
#! calculate the number of full grids
full_grids = m.floor(total_vids / (Xg * Yg))
#! calculate the number of full and partial grids
all_grids = m.ceil(total_vids / (Xg * Yg))

print(
    Fore.WHITE
    + f"Merging {total_vids} into {full_grids} {grid} grids with a partial grid of {remainder} videos"
)
"""
[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]
"""
#! create a 1D list of videos by row
vids = chunks(vids, Xg)
"""
[
    [1, 2], [3, 4], [5, 6], [7, 8], [9, 10], [11, 12], [13, 14], [15, 16]
]
"""
total_row_vids = len(vids)
#! create a 2D list of videos by col
vids = chunks(vids, Yg)
"""
[
    [   [ 1,  2], [ 3,  4]  ], 
    [   [ 5,  6], [ 7,  8]  ], 
    [   [ 9, 10], [11, 12]  ], 
    [   [13, 14], [15, 16]  ]
]
"""
total_col_vids = len(vids)

#! loop thru each row and pass row list to function i.s. merge_h( [[1, 2],[3, 4]] ...)
for i in range(len(vids)):
    print(Fore.WHITE + f"CREATING GRID {i+1}/{all_grids}")
    merge_h(vids[i], Xg, Yg, i, all_grids)

# cleanpost()
