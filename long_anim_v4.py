#!/bin/env python

from urllib import request
import os, sys, getopt
from glob import glob
import tempfile as tmp
import shutil
from pathlib import Path
import more_itertools
from colorama import init, Fore, Back
import subprocess
import websocket #! NOTE: websocket-client (https://github.com/websocket-client/websocket-client)
import uuid
import json
import urllib.request
import urllib.parse
from pprint import pprint
import calendar
import time
import toml
import re
import traceback
from playsound import playsound

init()
server_address = "127.0.0.1:8188"
client_id = str(uuid.uuid4())

def find_in_json(prompt,findkey):
    rstr = []
    for l1_key in prompt:
        L2 = prompt[l1_key]
        for l2_key in L2:
            L3 = L2[l2_key]
            if type(L3) == str:
                if L3 == findkey:
                    rstr.append(f"['{l1_key}']['{l2_key}']={L3}")
            if type(L3) == dict:
                for v in L3:
                    if v == findkey:
                        rstr.append(f"['{l1_key}']['{l2_key}']['{v}']={L3[v]}")
    return rstr
def split_path(pstr):
    dirname = os.path.dirname(pstr)

    if dirname == "" or dirname == ".":
        dirname = os.getcwd()
    basename = os.path.basename(pstr)
    ns = basename.split(".")
    ext = ns[-1]
    nameonly = "".join(ns[:-1])
    fullpath = f"{dirname}/{basename}"

    return {
        "dirname": dirname,
        "basename": basename,
        "ext": ext,
        "nameonly": nameonly,
        "fullpath": fullpath,
    }
def tryit(kwargs, arg, default):
    try:
        rs = kwargs[arg]
    except:
        rs = default
    return rs
def prunlive(cmd, **kwargs):
    # print("+++++++++++++",cmd)
    debug = tryit(kwargs, "debug", False)
    dryrun = tryit(kwargs, "dryrun", False)
    quiet = tryit(kwargs, "quiet", True)
    if dryrun == "print":
        prCmd(cmd)
        return

    scmd = cmd.split()
    # print("===========", scmd)
    for i in range(len(scmd)):
        scmd[i] = scmd[i].replace("~", " ")
        scmd[i] = scmd[i].replace('"', "")
    if debug:
        prSub(cmd)
        # pprint(scmd)

    process = subprocess.Popen(scmd, stdout=subprocess.PIPE)
    if quiet == True:
        for line in process.stdout:
            print(Fore.RED, end="")
            sys.stdout.write(line.decode("utf-8"))
            print(Fore.RESET, end="")
def get_timestamp():
    current_GMT = time.gmtime()
    time_stamp = calendar.timegm(current_GMT)
    return time_stamp
#! https://github.com/comfyanonymous/ComfyUI/blob/master/script_examples/websockets_api_example.py
def get_history(prompt_id):
    with urllib.request.urlopen("http://{}/history/{}".format(server_address, prompt_id)) as response:
        return json.loads(response.read())
def get_queue_id():
    prompt_id = queue_prompt(prompt)['prompt_id']
def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req =  urllib.request.Request("http://{}/prompt".format(server_address), data=data)
    return json.loads(urllib.request.urlopen(req).read())
#! https://github.com/comfyanonymous/ComfyUI/blob/master/script_examples/basic_api_example.py

def maketmpname(str,**kwargs):
    """
    Create a temp filename that is prefixed with a string.
    Optionally, create a directory
    """
    create = tryit(kwargs,'create',False)
    paths = split_path(tmp.mktemp())
    newname = f"{paths['dirname']}/{str}_{paths['basename']}"
    if create == True:
        os.mkdir(newname)
    return(newname)
def testpath(str):
    """
    Check if path exists, if not, create
    """
    if not os.path.exists(str):
        os.mkdir(str)
    return str
def get_sorted_files(spec):
    """
    return a sorted list of filenames
    """
    files = glob(spec)
    files = sorted(files)
    return files
def get_video_frames(video, config, **kwargs):
    """
    extract the frames of a video and return a sorted list of filenames
    """
    debug = tryit(kwargs,'debug',False)
    tmpdir = maketmpname("EXT",create=True)
    if debug: print(f"made dir: {tmpdir}")

    max_extracted_frames = config['params']['max_extracted_frames']
    nth = config['params']['everynth']

    if max_extracted_frames == 0:
        prInfo(f"Extracting [ALL] frames at [{fps}] from [{video}] to [{tmpdir}]")
        cmd = f"ffmpeg -y -loglevel warning -hwaccel cuda -i {video} -vf \"fps=8/1,scale={config['w']}:{config['h']}\"/  {tmpdir}/%04d.{IMF}"
    else:
        prInfo(f"Extracting [{max_extracted_frames}] frames from [{video}] to [{tmpdir}]")
        cmd = f"ffmpeg -y -loglevel warning -hwaccel cuda -i {video} -vf \"fps=8/1,scale={config['w']}:{config['h']}\" -vframes {max_extracted_frames} {tmpdir}/%04d.png"

    #! max_extracted_frames override
    #! calculate the number of frames to extract
    if config['params']['runtime'] > 0:
        max_extracted_frames = fps * config['params']['runtime']
        # prInfo(f"max_extracted_frames ({max_extracted_frames}) = int(({fps} * {groupsize}) + ({interpx} * ({config['params']['runtime']} / {groupsize}) - {groupsize}))")
        prInfo(f"OVERIDING max_extracted_frames' with runtime calculation of [{config['params']['runtime']}] secs = [{max_extracted_frames}] frames")
        cmd = f"ffmpeg -y -loglevel warning -hwaccel cuda -i {video} -vf \"fps={nth},scale={config['w']}:{config['h']}\" -vframes {max_extracted_frames} {tmpdir}/%04d.png"
        # procexit()

    prCmd(cmd)
    prunlive(cmd, debug = debug)

    files = get_sorted_files(f"{tmpdir}/*{IMF}")
    return files
def cleandir(dir):
    """
    delete all files in a dir
    """
    files = get_sorted_files(dir)

    # print(files)
    for f in files:
        if os.path.isfile(f):
            os.unlink(f)
        if os.path.isdir(f):
            shutil.rmtree(f)
def createInterps(last,first,**kwargs):
    """
    Create n interpoalted frames based on two existing frames.
    Return a list of newly created frames
    If debug==True, adds a red dot to teh interpolated frames
    """
    interpx = tryit(kwargs,'interpx',8)
    debug = tryit(kwargs,'debug',False)
    dot = tryit(kwargs,'dot',False)

    #! make target dirs
    indir = maketmpname("IN",create=True)
    if debug: print(f"made indir: {indir}")
    outdir = maketmpname("OUT",create=True)
    if debug: print(f"made outdir: {outdir}")

    #! copy first and last images to targets
    if debug: print(f"copying [{last}] => [{indir}/1.{IMF}]")
    shutil.copy(last,indir+f"/1.{IMF}")
    if debug: print(f"copying [{first}] => [{indir}/2.{IMF}]")
    shutil.copy(first,indir+f"/2.{IMF}")

    #! call interp script (runs in conda env 'rife')
    cmd = f"/home/jw/src/rife/simple_interp.sh {indir} {outdir} {interpx}"
    prunlive(cmd,debug=debug)

    files = get_sorted_files(f"{outdir}/*.{IMF}")
    if dot == True:
        prInfo(f"Adding red dot to interpolates transition frames")
        #! for debugging, mark interp images with icon
        from PIL import Image, ImageDraw, ImageFilter
        im2 = Image.open('/home/jw/share/dot512.png')
        for file in files:
            im1 = Image.open(file)
            back_im1 = im1.copy()
            back_im1.paste(im2, (10,10))
            back_im1.save(file, quality=95)

    return files, len(files)
def extract_video(video):
    """
    Extracts the frames from the generated video clips in subfolder specific to the video
    """
    parts = split_path(video)
    exdir = maketmpname(parts["nameonly"],create=True)
    #! extract to jpg to save GPU RAM?
    cmd = f"ffmpeg -y -loglevel panic -i {video}  -r {fps}/1 {exdir}/%04d.{IMF}"
    prunlive(cmd, debug=True)

    files_ary = get_sorted_files(f"{exdir}/*.{IMF}")
    return files_ary
def wait_until_finished(prompt_id):
    history = {}
    while(len(history)==0):
        history = get_history(prompt_id)
        print(".", end="", flush=True)
        time.sleep(5)
    print("\n")
    return True
def save_prompt(prompt,str,n):
    data = json.dumps(prompt, indent=4)
    with open(f"/home/jw/src/ComfyUI/output/__{str}_{n}.json", "w") as f:
        f.write(data)
def save_workflow(dir):
    swfile = f"{config['loc']['settings_dir']}/[01]_*"
    cmd = f"cp {swfile} {dir} "
    prCmd(cmd)
    os.system(cmd)
def bytesave_prompt(txt,stage,config):
    saveto = f"{config['loc']['settings_dir']}/{config['loc']['output_dir']}{config['version']}/prompt_{stage}_flat.txt"
    with open(saveto, "wb") as f:
            f.write(txt.encode())
    prInfo(f"SAVED PROMPT: [{saveto}]")
def update_template(prompt_text, i,config,stage):
    IMF=config['params']['imgfmt']
    w = config['w']
    h = config['h']

    if stage == "anim":
        cnets = config['prep']['cnets']
        for cnet in cnets:
            prompt_text = prompt_text.replace(f"{cnet}_00", f"{cnet}_{i:02d}")

        prompt_text = prompt_text.replace("OUTPUTVIDEONAME", f"{config['name']}")

        #! the values in the search terms act as the default values must match those set in the prep-API.json or anim.json_API workflow
        prompt_text = prompt_text.replace("\"batch_size\": 48,", f"\"image_load_cap\": {config['params']['groupsize']},")
        prompt_text = prompt_text.replace("\"image_load_cap\": 48,", f"\"image_load_cap\": {config['params']['groupsize']},")
        prompt_text = prompt_text.replace("\"frame_rate\": 8,", f"\"frame_rate\": {config['params']['fps']},")
        prompt_text = re.sub("\"steps\": 20,", f"\"steps\": {config['params']['steps']},",prompt_text)
        prompt_text = re.sub("\"width\": 256, \"height\": 144,", f"\"width\": {w}, \"height\": {h},", prompt_text)

        # ! changes just for prep
    if stage == "prep":
        # ! for prep dir names, which has the dirname slug '*_ZZ'
        prompt_text = prompt_text.replace("ZZ", f"{i:02d}")

        # ! make sure the CN 'resolution' is a multiple of 64, min 256, max 2880,
        cnres = int(config['w']/64)*64
        prompt_text = re.sub("\"resolution\": 256,", f"\"resolution\": {cnres},", prompt_text)

        #! For all the base IP images, rename to correct res:.  If the slug name is 'IMAGE00.png" in the JSON file
        #! and 'viking.png' in the TOML file, and the w/h params are 256/144, the new name is
        #! IPIMAGE00.png => 256x144_viking.png
        #! IPIMAGE01.png => 256x144_spagmin.png

        #!!! THE STUBS 'IPIMAGE_00.png' NEED TO BE MANUALLY EDITED IN THE JSON FILE !!!

        #! etc...
        for i in range(len(config['files']['IP_images'])):
            img = f"{config['files']['IP_images'][i]}.{IMF}"  #  base names: 'viking.png','spagmon.png'
            newname = f"{w}x{h}_{img}"
            prInfo(f"UPDATING IMAGE NAME: [IPIMAGE{i:02d}.{IMF}] => [{newname}] in {stage} template")
            prompt_text = re.sub(f"\"image\": \"IPIMAGE{i:02d}.{IMF}\",", f"\"image\": \"{newname}\",", prompt_text)


    jsonprompt = json.loads(prompt_text)
    for k in ["batch_size","image_load_cap","frame_rate","steps","image",]:
        rs = find_in_json(jsonprompt,k)
        for r in rs:
            prInfo(r)

    return jsonprompt

def flatten_json(text):
    j = json.loads(text)
    jflat = json.dumps(j)
    return jflat
def prCmd(cmd):
    """
    print Commands
    """
    print(">>> "+Fore.LIGHTCYAN_EX+cmd+Fore.RESET,flush=True)
def prInfo(info):
    """
    print Information
    """
    print(">>> "+Fore.LIGHTMAGENTA_EX+info+Fore.RESET,flush=True)
def prErr(err):
    """
    print Errors
    """
    print(">>> "+Fore.RED+err+Fore.RESET)
    print(">>> "+Fore.RED+"Abort Flag Set"+Fore.RESET,flush=True)
    traceback.print_stack()
    abort_flag(1)
    playsound("error.wav")
    exit()
def prAnn(ann):
    """
    print Announcements
    """
    print(">>> "+Fore.LIGHTCYAN_EX + ann + Fore.RESET,flush=True)

def prSub(sub):
    """
    print Subsustem Output
    """
    print(Fore.LIGHTBLUE_EX + sub + Fore.RESET,flush=True)

def is_abort():
    if os.path.isfile("/tmp/abort.flag"):
        return True
    else:
        return False
def abort_flag(stat):
    if stat == 0:
        if os.path.isfile("/tmp/abort.flag"): os.unlink("/tmp/abort.flag")
    else:
        os.system("touch /tmp/abort.flag")
        exit()

def procexit():
    abort_flag(1)
def saveparam(key,val):
    with open(f'/tmp/{key}.json', 'w') as f:
        f.write(json.dumps(val))
def loadparam(key):
    with open(f'/tmp/{key}.json', 'r') as f:
        val = json.load(f)
        return(val)

def upscale(outdir,config):
    files = get_sorted_files(f"{outdir}/*.{config['params']['imgfmt']}")
    ct = len(files)
    i = 1
    for file in files:
        cmd = f"./simple_upscale.sh {file} {config['params']['upscale']} {outdir}/out"
        # prCmd(cmd)
        print(f"{i}/{ct}",end="\r")
        prunlive(cmd)
        i+=1
    print("\n")
def showhelp():
    print("help")
    rs = """
    -h, --help          show help
    -v, --video         src video for CN preprocessing
    -d, --debug         
    -s, --stage         'prep'|'anim'|'merge'
    -x, --experimental  'fswap`|'dot'
    -D, --projdir       project directory
    -F, --flatprompt    dump flat prompt and exit
    -V, --version
    -u, --upscale

    -x, --experimental options
        'fswap'     use last frame of previous clip as seed image for following clip
        'dot'       add red dot in corner of all interpolated images
    """
    print(rs)
    procexit()

# v ────────────────────────────────────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if is_abort():
        print("Abort Flag: Terminating")
        procexit()

    argv = sys.argv[1:]

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
                        'upscale=',
                ],
        )
    except Exception as e:
        print(str(e))

    stage = False
    experimental_ary = []
    version = False
    for opt, arg in opts:
        if opt in ("-h", "--help"):showhelp()
        if opt in ("-D", "--projdir"):projdir = arg
        if opt in ("-s", "--stage"):stage = arg
        if opt in ("-V", "--version"):version = arg

    if stage == False:
        print("-s, --stage missing")
        showhelp()
    if projdir == False:
        print("-D, --projdir missing")
        showhelp()
    if version == False:
        print("-V, --version missing")
        showhelp()


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

    settings_dir = f"{config['loc']['settings_dir']}"
    prInfo(f"settings_dir = [{settings_dir}]")

    output_dir = testpath(f"{settings_dir}/{config['loc']['output_dir']}{projver}")
    prInfo(f"output_dir = [{output_dir}]")

    input_dir = testpath(f"{settings_dir}/{config['loc']['input_dir']}{projver}")
    prInfo(f"input_dir = [{input_dir}]")

    # xvideoname = f"{config['w']}x{config['h']}_{config['files']['video']}"
    video = f"{settings_dir}/{w}x{h}_{config['files']['video']}"
    prInfo(f"INPUT VIDEO = [{video}]")

    flatprompt = False # debugging flag
    fswap = False # experimental flag
    dot = False # experimental flag
    upscale_frames = False

    #! output from the START command
    hideSTDOUT = "2>&1 >> /tmp/START.log"
    if debug == True:
        hideSTDOUT = ""

    for opt, arg in opts:
        if opt in ("-v", "--video"):video = arg
        if opt in ("-d", "--debug"):debug = True
        if opt in ("-a", "--atmpl"):anim_template_name = arg
        if opt in ("-F", "--flatprompt"):flatprompt = True
        if opt in ("-u", "--upscale"):upscale_frames = True
        if opt in ("-x", "--experimental"):
            experimental_ary = arg.split(",")
            if "fswap" in experimental_ary:
                fswap = True
            if "dot" in experimental_ary:
                dot = True


    if stage == False:
        print("-s, --stage missing")
        showhelp()

    #----------------------------------------------------------------------------------------

    timestamp = get_timestamp()
    cleandir(f"{os.environ['TMPDIR']}/*")
    fgroups_ct = 0

    #! save copies of the workflows in the output dir
    save_workflow(output_dir)

    #! pre-loop setup
    if stage == "prep":
        prInfo(f"Extracting [{config['params']['fps']}] fps frames from [{video}]")
        files = get_video_frames(video, config)

        prInfo(f"Extracted [{len(files)}] from [{video}]")
        prInfo(f"groupsize = {groupsize}")
        fgratio = len(files) / groupsize
        prInfo(f"fgratio = {fgratio}")

        # ! make sure there are at least 2 groups
        if int(fgratio) < 2:
            prErr(f"ER:00 - There are not enough frames for more than 1 group (fg-ratio: {fgratio})")
            # new_groupsize = (int(len(files) / 2))
            # prErr(f"ER:01 - Lowering groupsize to {new_groupsize}")
            # groupsize = new_groupsize


        # ! now split into groups
        fgroups = list(more_itertools.chunked(files[:(groupsize*int(fgratio))], groupsize)) #! limit array to not create 'fractional' groups
        fgroups_ct = len(fgroups)
        saveparam("fgroups_ct",fgroups_ct)
        saveparam("fgroups",fgroups)

        # ! manually increase fgroups_ct
        # fgroups_ct = 10

        prInfo(f"Created [{fgroups_ct}] groups of [{groupsize}] from [{len(files)}] frames")

        # target_input = f"/home/jw/src/ComfyUI/INPUTS/{projname}-input"
        # target_output = f"/home/jw/src/ComfyUI/output/{projname}"

        #! only clean output_dir when prepping
        prInfo(f"Cleaning [{output_dir}/*]")
        cleandir(f"{output_dir}/*")
    else:
        fgroups_ct = loadparam("fgroups_ct")
        fgroups = loadparam("fgroups")

    if stage == "anim":
        tdirs = [] # stub ary to hold group folder names; 00, 01, 02

        #! delete previous output FILES (not dirs) that start with project_name in output_dir
        ftypes = ["mp4","png","jpg"]
        for t in ftypes:
            pfs = glob(f"{output_dir}/{projname}*.{t}")
            for pf in pfs:
                os.unlink(pf)
        #! copy all images to input
        cmd = f"cp {settings_dir}/*.{IMF} {output_dir}"
        prInfo(cmd)
        os.system(cmd)
        cmd = f"cp {settings_dir}/*.{IMF} {output_dir}"
        prCmd(cmd)
        os.system(cmd)
    # if os.path.exists(target_input):
        #     prInfo(f"[{target_input}] Exists... Deleting")
        #     shutil.rmtree(target_input)
        # os.mkdir(target_input)
    #! symlink to 'inputs'
    # if os.path.exists(config['loc']['input_dir']):
    #     os.unlink(config['loc']['input_dir'])
    # cmd = f"ln -fs {target_input}/ {config['loc']['input_dir']}"
    # prCmd(cmd)
    # os.system(cmd)
    # exit()

    #! MAIN LOOP -------------------------------------------------------------- start Comfy
    if stage != "merge":  #! 'merge' does not use/need Comfy.
        cmd = f"/home/jw/src/ComfyUI/START  -i {input_dir} -o {output_dir}  {hideSTDOUT} &"
        prCmd(cmd)
        os.system(cmd)
        time.sleep(20) #! hardcoded as I don't know how to test for when ready

    #! fgroupod determines how many clips are made and is calulated by the CN frames.
    #! Manully override by
    prInfo(f"CREATING [{fgroups_ct}] GROUPS")

    for i in range(start_at_fgroup, fgroups_ct):
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
            prompt_flat = flatten_json(prompt_text)
            if flatprompt == True:
                bytesave_prompt(prompt_flat,stage,config)
            prompt = update_template(prompt_text,i,config,stage)
            prompt_id = queue_prompt(prompt)['prompt_id']

            #! WAIT FOR THE QUEUE TO COMLETE
            wait_until_finished(prompt_id)


            #! move oputput files to input folder
            # pfs = glob("/home/jw/src/ComfyUI/output/*_*")
            # for pf in pfs:
                # parts = split_path(pf)  # dirname # basename # ext # nameonly # fullpath
                # cmd = f"mv {pf} {target_input}"
                # prCmd(cmd)
                # os.system(cmd)


        if stage == "anim":
            # prInfo(f"ANIM LOOP: [{i}/{ fgroups_ct - 1}]")
            # ! due to memory (or something) issues, need to restart Comfy for each iteration of the loop
            cmd = f"/home/jw/src/ComfyUI/START  -i {input_dir} -o {output_dir} {hideSTDOUT} &"
            prCmd(cmd)
            os.system(cmd)
            time.sleep(20) #! hardcoded as I don't know how to test for when ready

            print(Fore.YELLOW + f"═════════════════════════════════════════════════[ ANIM {i}/{fgroups_ct}]════" + Fore.RESET)
            #! create folder by group; 00, 01, 02, ...
            tmpdir = f"{os.environ['TMPDIR']}/{i:02d}"
            prInfo(f"Target (tmpdir): [{tmpdir}]")
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
            prompt_flat = flatten_json(prompt_text)
            if flatprompt == True:
                bytesave_prompt(prompt_flat,stage,config)

            prompt = update_template(prompt_flat,i,config,stage)

            #! this is where we assign the new seed image as the last image of the previous group
            if fswap:
                if i > 0:
                    newseed = f"{tdirs[i-1]}/{groupsize:03d}.{IMF}"
                    prompt['30']['inputs']['image']=newseed
                    if debug:
                        prInfo(f"Setting seed image to [{newseed}]")

            # save_prompt(prompt_flat,stage,i)
            # print(prompt_flat)
            # exit()

            prompt_id = queue_prompt(prompt)['prompt_id']

            #! WAIT FOR THE QUEUE TO COMLETE
            wait_until_finished(prompt_id)

            if i >= config['params']['maxloops']:
                prInfo(f"[{i}] > [{config['params']['maxloops']}].....  Breaking Loop!")
                break
        #! copy output files to project output folder.  They are copied, not moved, because Comfy needs to
        #! see which files already exist so as to name them correctly.
        # cmd = f"cp  /home/jw/src/ComfyUI/output/{projname}_* {target_output}"
        # prCmd(cmd)
        # os.system(cmd)
    #!end of loop

    if stage == "merge":
        print(Fore.YELLOW+f"═════════════════════════════════════════════════[ MERGE ]════"+Fore.RESET)
        allfiles = [] # stub for storage of all files
        exdirimgs_ary = [] # stub for storage of all clip files

        #! get list if video clips in sorted order
        vid_clips_ary = get_sorted_files(f"{output_dir}/{mp4_output_wc}")
        prInfo(f"Loaded [{len(vid_clips_ary)}] clips")

        if len(vid_clips_ary) < 2:
            prErr(f"ER:02 - Only 1 clip exists")
            exit()

        prInfo(f"Looping over [{len(vid_clips_ary)}] clips")
        for clip in vid_clips_ary:
            extracted_frames_ary = extract_video(clip)
            prInfo(f"\tExtracted [{len(extracted_frames_ary)}] frames from [{clip}]")
            exdirimgs_ary.append(extracted_frames_ary)
        #! all files for a specific clip are now in one folder
        for j in range(len(exdirimgs_ary)):
            try:
                #! add clip images to final 1D 'allfiles' ary
                # print(len(exdirimgs_ary[j]))
                allfiles.append(exdirimgs_ary[j])
                prInfo(f"Added [{len(exdirimgs_ary[j])}] src files from clip [{j}]")
                last = exdirimgs_ary[j][-1]
                first = exdirimgs_ary[j+1][0]

                prInfo(f"Interpolating: {last} <=> {first} {interpx}x")
                newfiles_ary, newfiles_ct = createInterps(last,first, interpx=interpx,debug=debug,dot=dot)#"dot" in set(experimental_ary))
                prInfo(f"Added [{newfiles_ct}] interp files")
                #! add the new files to the end of ary
                allfiles.append(newfiles_ary)
            except:
                pass
        total_frames = 0
        for k in allfiles:
            total_frames += len(k)

        prInfo(f"TOTAL FRAMES: [{total_frames}]")

        #! now rename in sequence
        tmpdir = maketmpname("FINAL",create=True)
        k = 0
        for group in allfiles:
            for filename in group:
                shutil.move(filename,f"{tmpdir}/{k:04d}.{IMF}")
                k += 1

        if upscale_frames == True:
            upscale(tmpdir,config)
            tmpdir = f"{tmpdir}/out"

        cmd = f"ffmpeg  -y -loglevel warning  -hide_banner -hwaccel auto -y -framerate {fps} -pattern_type glob -i {tmpdir}/*.{IMF}  -r {fps} -vcodec libx264 -preset medium -crf 23 -vf minterpolate=mi_mode=blend,fifo -pix_fmt yuv420p  -movflags +faststart  {output_dir}/final.mp4"
        prunlive(cmd,debug=debug)
        prAnn(f"FINAL VIDEO:\nmpv {output_dir}/final.mp4")
        playsound("finished.wav")

    #! cleanup after loop
    #! remove all the copied mp4.
    # if stage == "anim":
    #     cmd = f"rm   /home/jw/src/ComfyUI/output/{projname}_*"
    #     print(cmd)
    #     os.system(cmd)

