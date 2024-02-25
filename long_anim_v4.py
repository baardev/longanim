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
    -v, --video         src video for CN preprocessing
    -d, --debug         flag
    -s, --stage         'prep'|'anim'|'merge'
    -x, --experimental  'fswap'|'dot'
    -D, --projdir       project directory
    -F, --flatprompt    dump flat prompt and exit
    -V, --version       '256','512','960'...
    -u, --upscale       flag

Notes:
    -x, --experimental options
        'fswap'     use last frame of previous clip as seed image for following clip
        'dot'       add red dot in corner of all interpolated images
    -F, --flatprompt     wite a non-indented JSON file of the workflow to the output directory    

    """
    print(rs)
    p.procexit()


# v ────────────────────────────────────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if p.is_abort():
        p.prErr("Abort Flag: Terminating")
        p.procexit()

    argv = sys.argv[1:]
    opts = False
    projdir = False
    try:
        opts, args = getopt.getopt(
            argv,
            "hv:ds:a:x:D:FV:u",
            [   'help',
                        'video=',
                        'debug',
                        'stage=',
                        'atmpl=',
                        'experimental=',
                        'projdir=',
                        'flatprompt',
                        'version=',
                        'upscale',
                ],
        )
    except Exception as e:
        print(str(e))

    stage = False
    experimental_ary = []
    version = False
    for opt, arg in opts:
        if opt in ("-h", "--help"):p.showhelp()
        if opt in ("-D", "--projdir"):projdir = arg
        if opt in ("-s", "--stage"):stage = arg
        if opt in ("-V", "--version"):version = arg

    if stage == False:
        print("-s, --stage missing")
        p.showhelp()
    if projdir == False:
        print("-D, --projdir missing")
        p.showhelp()
    if version == False:
        print("-V, --version missing")
        p.showhelp()


    #! from TOML
    # with open(f"{projdir}/{version}_anim.toml", 'r') as f:  config = toml.load(f)
    with open(f"{projdir}/0_anim.toml", 'r') as f:  config = toml.load(f)

    os.environ["TMPDIR"] = config['loc']['tmpdir']
    w = config['w']
    h = config['h']
    debug = config['params']['debug']
    projname = config['name']
    projver = config['version']
    anim_template_name = config['files']['anim_template_name'] # "workflow_api.json"
    prep_template_name = config['files']['prep_template_name'] #"stitcher_prep_stage_960_API.json"
    mp4_output_wc = f"{projname}{config['specs']['mp4_output_wc']}" #"mandala_flower_?????.mp4"
    groupsize = config['params']['groupsize'] # anim
    interpx = config['params']['interpx'] # merge
    overlap = config['params']['overlap'] # deprecated
    fps = config['params']['fps']
    IMF = config['params']['imgfmt']
    start_at_fgroup = config['params']['start_at_fgroup']

    #! constructed vars, saved in 'config'
    settings_dir = f"{config['loc']['settings_dir']}/{projname}"
    config['xsettings_dir']=settings_dir
    p.prInfo(f"settings_dir = [{settings_dir}]")

    output_dir = p.testpath(f"{settings_dir}/{config['loc']['output_dir']}{projver}")
    config['xoutput_dir']=output_dir
    p.prInfo(f"output_dir = [{output_dir}]")

    input_dir = p.testpath(f"{settings_dir}/{config['loc']['input_dir']}{projver}")
    config['xinput_dir']=input_dir
    p.prInfo(f"input_dir = [{input_dir}]")

    # xvideoname = f"{config['w']}x{config['h']}_{config['files']['video']}"
    video = f"{settings_dir}/{w}x{h}_{config['files']['video']}"
    config['xvideo']=video
    p.prInfo(f"INPUT VIDEO = [{video}]")

    flatprompt = False # debugging flag
    fswap = False # experimental flag
    dot = False # experimental flag
    upscale_video = False

    #! output from the START command
    hideSTDOUT = "2>&1 >> /tmp/START.log"
    if debug == True:
        hideSTDOUT = ""

    for opt, arg in opts:
        if opt in ("-v", "--video"):video = arg
        if opt in ("-d", "--debug"):debug = True
        if opt in ("-a", "--atmpl"):anim_template_name = arg
        if opt in ("-F", "--flatprompt"):flatprompt = True
        if opt in ("-u", "--upscale"):upscale_video = True
        if opt in ("-x", "--experimental"):
            experimental_ary = arg.split(",")
            if "fswap" in experimental_ary:
                fswap = True
            if "dot" in experimental_ary:
                dot = True


    if stage == False:
        print("-s, --stage missing")
        p.showhelp()

    #----------------------------------------------------------------------------------------

    timestamp = p.get_timestamp()
    p.cleandir(f"{os.environ['TMPDIR']}/*")
    fgroups_ct = 0

    #! pre-loop setup
    if stage == "prep":
        #! restart server here as prep does not to to restart in the loop, like admin
        p.prInfo("Restarting Server")
        cmd = f"./START  -i {input_dir} -o {output_dir} {hideSTDOUT} &"
        p.prCmd(cmd)
        os.system(cmd)
        # ! wait for server to be up
        p.wait_for_server()


        p.prInfo(f"Extracting [{config['params']['fps']}] fps frames from [{video}]")
        files = p.get_video_frames(video, config)

        p.prInfo(f"Extracted [{len(files)}] from [{video}]")
        p.prInfo(f"groupsize = {groupsize}")
        fgratio = len(files) / groupsize
        p.prInfo(f"fgratio = {fgratio}")

        # ! make sure there are at least 2 groups
        if int(fgratio) < 2:
            p.prErr(f"ER:00 - There are not enough frames for more than 1 group (fg-ratio: {fgratio})")

        # ! now split into groups
        fgroups = list(more_itertools.chunked(files[:(groupsize*int(fgratio))], groupsize)) #! limit array to not create 'fractional' groups
        fgroups_ct = len(fgroups)
        p.saveparam("fgroups_ct",fgroups_ct)
        p.saveparam("fgroups",fgroups)

        p.prInfo(f"Created [{fgroups_ct}] groups of [{groupsize}] from [{len(files)}] frames")

        #! only clean output_dir when prepping
        p.prInfo(f"Cleaning [{output_dir}/*]")
        p.cleandir(f"{output_dir}/*")
    else:
        fgroups_ct = p.loadparam("fgroups_ct")
        fgroups = p.loadparam("fgroups")

    tdirs = []  #! stub ary to hold group folder names; 00, 01, 02
    if stage == "anim":
        #! delete previous output FILES (not dirs) that start with project_name in output_dir
        ftypes = ["mp4","png","jpg"]
        for t in ftypes:
            pfs = glob(f"{output_dir}/{projname}*.{t}")
            for pf in pfs:
                os.unlink(pf)
        #! copy all images to input
        cmd = f"cp {settings_dir}/*.{IMF} {output_dir}"
        p.prInfo(cmd)
        os.system(cmd)
        cmd = f"cp {settings_dir}/*.{IMF} {output_dir}"
        p.prCmd(cmd)
        os.system(cmd)

    #! fgroupod determines how many clips are made and is calulated by the CN frames.
    #! Manully override by
    p.prInfo(f"CREATING [{fgroups_ct}] GROUPS")

    #! MAIN LOOP -------------------------------------------------------------- start Comfy
    p.prInfo("Entering MAIN LOOP")
    for i in range(start_at_fgroup, fgroups_ct):
        # prep
        if stage == "prep":
            print(Fore.YELLOW + f"═════════════════════════════════════════════════[ PREP {i}/{fgroups_ct}]════" + Fore.RESET)

            #! Save fgropups to dir/file
            #! this is a try in case fgroups has been manually altered (in which case this will fail)
            try:
                tmpdir = f"{os.environ['TMPDIR']}/{i:02d}"
                os.makedirs(tmpdir)
                for j in range(0,len(fgroups[i])):
                    shutil.copy(fgroups[i][j], tmpdir + f"/{(j+1):03d}.{IMF}")
            except:
                pass

            #! load and run prep template prompt,  This creates the ControNet input images in 'output_dir'
            prompt_text = Path(f"{settings_dir}/{prep_template_name}").read_text()
            if flatprompt == True:
                p.bytesave_prompt(prompt_text,stage,config)
            p.prInfo("Updating Template in 'prep'")
            prompt = p.update_template(prompt_text,i,config,stage)
            p.prInfo("Submitting PREP workflow")
            prompt_id = p.queue_prompt(prompt)['prompt_id']
            p.prInfo(f"Prompt ID: [{prompt_id}]")

            #! WAIT FOR THE QUEUE TO COMLETE
            p.wait_until_finished(prompt_id)

        if stage == "anim":
            # anim
            # ! due to memory (or something) issues, need to restart Comfy for each iteration of the loop
            cmd = f"./START  -i {input_dir} -o {output_dir} {hideSTDOUT} &"
            p.prCmd(cmd)
            os.system(cmd)

            #! wait for server to be up
            p.wait_for_server()

            print(Fore.YELLOW + f"═════════════════════════════════════════════════[ ANIM {i}/{fgroups_ct}]════" + Fore.RESET)
            #! create folder by group; 00, 01, 02, ...
            tmpdir = f"{os.environ['TMPDIR']}/{i:02d}"
            p.prInfo(f"Target (tmpdir): [{tmpdir}]")
            os.mkdir(tmpdir)
            tdirs.append(tmpdir)

            #! copy and rename/renumber subset of files to folder
            try:
                for j in range(0,len(fgroups[i])):
                    shutil.copy(fgroups[i][j], f"{tmpdir}/{(j+1):03d}.{IMF}")
            except:
                pass

            #! submit the prompt
            prompt_text = Path(f"{settings_dir}/{anim_template_name}").read_text() #! load template

            prompt = p.update_template(prompt_text,i,config,stage)

            #! this is where we assign the new seed image as the last image of the previous group
            if fswap:
                if i > 0:
                    newseed = f"{tdirs[i-1]}/{groupsize:03d}.{IMF}"
                    prompt['30']['inputs']['image']=newseed
                    if debug:
                        p.prInfo(f"Setting seed image to [{newseed}]")

            #!  ?? for some reason, the server is not up at this point, even though it passed the previous gate
            p.wait_for_server()
            try:
                prompt_id = p.queue_prompt(prompt)['prompt_id']
                p.prInfo(f"Prompt ID: [{prompt_id}]")
                # ! WAIT FOR THE QUEUE TO COMPLETE
                p.wait_until_finished(prompt_id)
            except Exception as e:
                print(str(e))
                p.abort_flag(1)

            if i >= config['params']['maxloops']:
                p.prInfo(f"[{i}] > [{config['params']['maxloops']}].....  Breaking Loop!")
                break

            # prompt_flat = flatten_json(prompt_text)
            if flatprompt == True:
                p.bytesave_prompt(prompt_text,stage,config)

    #!end of loop

    if stage == "merge":
        # merge
        print(Fore.YELLOW+f"═════════════════════════════════════════════════[ MERGE ]════"+Fore.RESET)
        #! get the updated counter ID here from 'counter.json' so as not step on anim loop dirs
        fileid = f"{p.increment_counter(config):02d}"
        p.prInfo(f"Current file ID = [{fileid}]")

        allfiles = [] #! stub for storage of all files
        exdirimgs_ary = [] #! stub for storage of all clip files

        #! get list if video clips in sorted order
        vid_clips_ary = p.get_sorted_files(f"{output_dir}/{mp4_output_wc}")
        p.prInfo(f"Loaded [{len(vid_clips_ary)}] clips")

        if len(vid_clips_ary) < 2:
            p.prErr(f"ER:02 - Only 1 clip exists")
            exit()

        p.prInfo(f"Looping over [{len(vid_clips_ary)}] clips")
        for clip in vid_clips_ary:
            extracted_frames_ary = p.extract_video(clip,config)
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
                newfiles_ary, newfiles_ct = p.createInterps(last,first, config,interpx=interpx,debug=debug,dot=dot)#"dot" in set(experimental_ary))
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
                shutil.move(filename,f"{tmpdir}/{k:04d}.{IMF}")
                k += 1

        cmd = f"ffmpeg  -y -loglevel warning  -hide_banner -hwaccel auto -y -framerate {fps} -pattern_type glob -i {tmpdir}/*.{IMF}  -r {fps} -vcodec libx264 -preset medium -crf 23 -vf minterpolate=mi_mode=blend,fifo -pix_fmt yuv420p  -movflags +faststart  {output_dir}/final.mp4"
        p.prunlive(cmd,debug=debug)
        p.prAnn(f"FINAL VIDEO:\nmpv {output_dir}/final.mp4")

        p.playsound("finished.wav")

        if upscale_video == True:
            p.upscale_v(output_dir,config)
            p.prAnn(f"FINAL UPSCALED VIDEO:\nmpv {output_dir}/upscaled/final.mp4")

        # ! save copies of the workflows in the output dir
        p.save_workflow(output_dir, settings_dir, fileid)

        p.playsound("finished.wav")
        p.playsound("finished.wav")

    #! cleanup after loop
    #! remove all the copied mp4.
    # if stage == "anim":
    #     cmd = f"rm   /home/jw/src/ComfyUI/output/{projname}_*"
    #     print(cmd)
    #     os.system(cmd)

