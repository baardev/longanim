#!/bin/env python

import long_anim_lib as p
import os
import sys
import getopt
from glob import glob
import shutil
from pathlib import Path
import more_itertools
from colorama import init, Fore
import toml
init()


def showhelp():
    print("help")
    rs = """
    -h, --help          show help
    -v, --videos        folder of videos to merge (def: pwd)
    -d, --debug         flag
    -x, --interpx       interp x frames (def: 12)
    -f, --fps           def:15
    -o, --output        output dir (def: <videos dir>)

    ./mergeclips.py --videos <input dir>


    """
    print(rs)
    exit()
def extract_video(video,fps):
    IMF = "png"

    """
    Extracts the frames from the generated video clips in subfolder specific to the video
    """
    parts = p.split_path(video)
    exdir = p.maketmpname(parts["nameonly"],create=True)
    #! extract to jpg to save GPU RAM?
    cmd = f"ffmpeg -y -loglevel panic -i {video}  -r {fps}/1 {exdir}/%04d.{IMF}"
    p.prunlive(cmd, debug=True)

    files_ary = p.get_sorted_files(f"{exdir}/*.png")
    return files_ary

def createInterps(last,first,**kwargs):
    IMF = "png"
    """
    Create n interpoalted frames based on two existing frames.
    Return a list of newly created frames
    If debug==True, adds a red dot to teh interpolated frames
    """
    interpx = p.tryit(kwargs,'interpx',8)
    debug = p.tryit(kwargs,'debug',False)

    #! make target dirs
    indir = p.maketmpname("IN",create=True)
    p.prInfo(f"made indir: {indir}")
    outdir = p.maketmpname("OUT",create=True)
    p.prInfo(f"made outdir: {outdir}")

    #! copy first and last images to targets
    p.prInfo(f"copying [{last}] => [{indir}/1.{IMF}]")
    shutil.copy(last,indir+f"/1.{IMF}")
    p.prInfo(f"copying [{first}] => [{indir}/2.{IMF}]")
    shutil.copy(first,indir+f"/2.{IMF}")

    #! call interp script (runs in conda env 'rife')
    cmd = f"/home/jw/src/longanim/simple_interp_images.sh {indir} {interpx} {outdir}" #JWFIX
    p.prCmd(cmd)
    p.prunlive(cmd,debug=debug)

    files = p.get_sorted_files(f"{outdir}/*.{IMF}")

    return files, len(files)



# v ────────────────────────────────────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    os.environ["TMPDIR"] = "/fstmp"
    p.cleandir(f"{os.environ['TMPDIR']}/*")

    vdir = os.getcwd()
    output_dir = vdir
    interpx = 12
    fps = 15
    debug=False

    argv = sys.argv[1:]
    opts = False
    try:
        opts, args = getopt.getopt(
            argv,
            "hv:dx:f:o:",
            [   'help',
                        'video_dir=',
                        'debug',
                        'interpx',
                        'fps',
                        'output',
                ],
        )
    except Exception as e:
        print(str(e))

    for opt, arg in opts:
        if opt in ("-h", "--help"): showhelp()
        if opt in ("-v", "--video_dir"):
            vdir = arg
            output_dir = arg
        if opt in ("-d", "--stage"): debug = True
        if opt in ("-x", "--interpx"): interpx = int(arg)
        if opt in ("-o", "--output"): output_dir = arg
    # merge
    print(Fore.YELLOW+f"═════════════════════════════════════════════════[ MERGE ]════"+Fore.RESET)
    allfiles = [] #! stub for storage of all files
    exdirimgs_ary = [] #! stub for storage of all clip files

    #! get list if video clips in sorted order
    vid_clips_ary = p.get_sorted_files(f"{vdir}/*.mp4")
    p.prInfo(f"Loaded [{len(vid_clips_ary)}] clips")

    if len(vid_clips_ary) < 2:
        p.prErr(f"ER:02 - Only 1 clip exists")
        exit()

    p.prInfo(f"Looping over [{len(vid_clips_ary)}] clips")
    for clip in vid_clips_ary:
        extracted_frames_ary = extract_video(clip,15)
        p.prInfo(f"\tExtracted [{len(extracted_frames_ary)}] frames from [{clip}]")
        exdirimgs_ary.append(extracted_frames_ary)

    #! all files for a specific clip are now in their own folders
    for j in range(len(exdirimgs_ary)):
        try:
            #! add clip images to final 1D 'allfiles' ary
            allfiles.append(exdirimgs_ary[j])
            p.prInfo(f"Added [{len(exdirimgs_ary[j])}] src files from clip [{j}]")
            last = exdirimgs_ary[j][-1]
            first = exdirimgs_ary[j+1][0]

            p.prInfo(f"Interpolating: {last} <=> {first} {interpx}x")
            newfiles_ary, newfiles_ct = createInterps(last,first,interpx=interpx,debug=debug)
            p.prInfo(f"Added [{newfiles_ct}] interp files")
            #! add the new files to the end of ary
            allfiles.append(newfiles_ary)
        except:
            pass
    total_frames = 0
    for k in allfiles:
        total_frames += len(k)

    p.prInfo(f"TOTAL FRAMES: [{total_frames}]")

    #! now rename in sequence
    tmpdir = p.maketmpname("FINAL",create=True)
    k = 0
    for group in allfiles:
        for filename in group:
            shutil.move(filename,f"{tmpdir}/{k:04d}.png")
            k += 1

    cmd = f"ffmpeg  -y -loglevel warning  -hide_banner -hwaccel auto -y -framerate {fps} -pattern_type glob -i {tmpdir}/*.png  -r {fps} -vcodec libx264 -preset medium -crf 23 -vf minterpolate=mi_mode=blend,fifo -pix_fmt yuv420p  -movflags +faststart  {output_dir}/final.mp4"
    p.prunlive(cmd,debug=debug)
    p.prAnn(f"FINAL VIDEO:\nmpv {output_dir}/final.mp4")

    p.playsound("~/src/longanim/finished.wav")

    # if upscale_video == True:
    #     p.upscale_v(output_dir,config)
    #     p.prAnn(f"FINAL UPSCALED VIDEO:\nmpv {output_dir}/upscaled/final.mp4")

    # ! save copies of the workflows in the output dir
    # p.save_workflow(output_dir, settings_dir, fileid)

    p.playsound("finished.wav")
    p.playsound("finished.wav")

