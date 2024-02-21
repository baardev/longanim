#!/bin/env python

from urllib import request
import requests
import os
import sys
from glob import glob
import tempfile as tmp
import shutil
from colorama import init, Fore
import subprocess
import uuid
import json
import urllib.request
import urllib.parse
import calendar
import time
import re
import traceback
#from playsound import playsound

init()
server_address = "127.0.0.1:8188"
client_id = str(uuid.uuid4())
def find_in_json(prompt, findkey):
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
def playsound(sfile):
    cmd = f"aplay {sfile}"
    os.system(cmd)
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
    fps = config['params']['fps']
    IMF = config['params']['imgfmt']
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
def createInterps(last,first,config,**kwargs):
    IMF = config['params']['imgfmt']
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
    cmd = f"/home/jw/src/rife/simple_interp_images.sh {indir} {interpx} {outdir}" #JWFIX
    prCmd(cmd)
    prunlive(cmd,debug=debug)

    files = get_sorted_files(f"{outdir}/*.{IMF}")
    if dot == True:
        prInfo(f"Adding red dot to interpolates transition frames")
        #! for debugging, mark interp images with icon
        from PIL import Image
        im2 = Image.open('/home/jw/share/dot512.png') #JWFIX
        for file in files:
            im1 = Image.open(file)
            back_im1 = im1.copy()
            back_im1.paste(im2, (10,10))
            back_im1.save(file, quality=95)

    return files, len(files)
def extract_video(video,config):
    fps = config['params']['fps']
    IMF = config['params']['imgfmt']

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
    with open(f"/home/jw/src/ComfyUI/output/__{str}_{n}.json", "w") as f: #JWFIX
        f.write(data)
def save_workflow(output_dir,settings_dir,fileid):
    newdir = f"{output_dir}/{fileid}"
    #! this dir should never already exist, so no need to check
    os.mkdir(newdir)
    #! copy all files that start with 0_ or 1_
    swfile = f"{settings_dir}/[01]_*"
    cmd = f"cp {swfile} {newdir} "
    prCmd(cmd)
    os.system(cmd)

    #! copy all MP4s
    swfile = f"{output_dir}/final.mp4"
    cmd = f"cp {swfile} {newdir} "
    prCmd(cmd)
    os.system(cmd)


def bytesave_prompt(prompt_text,stage,config):
    prompt_flat = flatten_json(prompt_text)
    saveto = f"{config['xoutput_dir']}/prompt_{stage}_flat.txt"
    with open(saveto, "wb") as f:
            f.write(prompt_flat.encode())
    prInfo(f"SAVED PROMPT: [{saveto}]")


def vrep(tfrom, tto, txt):
    txt = re.sub(tfrom, tto, txt)
    prInfo(f"REPLACED: [{tfrom}] => [{tto}]")
    return txt


def update_template(prompt_text, i,config,stage):

    prompt_text = flatten_json(prompt_text)
    IMF=config['params']['imgfmt']
    w = config['w']
    h = config['h']

    if stage == "anim":
        cnets = config['prep']['cnets']
        for cnet in cnets:
            prompt_text = prompt_text.replace(f"{cnet}_00", f"{cnet}_{i:02d}")

        prompt_text = prompt_text.replace("OUTPUTVIDEONAME", f"{config['name']}")

        #! the values in the search terms act as the default values must match those set in the prep-API.json or anim.json_API workflow

        prompt_text = vrep('"batch_size": 48,', f'"image_load_cap": {config["params"]["groupsize"]},',prompt_text)
        prompt_text = vrep('"frame_rate": 8,', f'"frame_rate": {config["params"]["fps"]},',prompt_text)
        prompt_text = vrep('"steps": 20,', f'"steps": {config["params"]["steps"]},',prompt_text)
        prompt_text = vrep('"width": 256, "height": 144,', f'"width": {w}, "height": {h},', prompt_text)

        for i in range(len(config['files']['IP_images'])):
            img = f"{config['files']['IP_images'][i]}.{IMF}"  #  base names: 'viking.png','spagmon.png'
            newname = f"{w}x{h}_{img}"
            #!  FIX THIS... not sure which is correct
            prompt_text = vrep(f'"image": "IPIMAGE{i:02d}.{IMF}",', f'"image": "{newname}",', prompt_text)
            prompt_text = vrep(f'"image": "IPIMAGE_{i:02d}.{IMF}",', f'"image": "{newname}",', prompt_text)

        # ! changes just for prep
    if stage == "prep":
        # ! for prep dir names, which has the dirname slug '*_ZZ'
        prompt_text = prompt_text.replace("ZZ", f"{i:02d}")

        # ! make sure the CN 'resolution' is a multiple of 64, min 256, max 2880,
        cnres = int(config['w']/64)*64
        # prompt_text = re.sub("\"resolution\": 256,", f"\"resolution\": {cnres},", prompt_text)
        prompt_text = vrep('"resolution": 256,', f'"resolution": {cnres},', prompt_text)



        #! For all the base IP images, rename to correct res:.  If the slug name is 'IMAGE00.png" in the JSON file
        #! and 'viking.png' in the TOML file, and the w/h params are 256/144, the new name is
        #! IPIMAGE00.png => 256x144_viking.png
        #! IPIMAGE01.png => 256x144_spagmin.png

        #!!! THE STUBS 'IPIMAGE_00.png' NEED TO BE MANUALLY EDITED IN THE JSON FILE !!!

        #! etc...
        # for i in range(len(config['files']['IP_images'])):
        #     img = f"{config['files']['IP_images'][i]}.{IMF}"  #  base names: 'viking.png','spagmon.png'
        #     newname = f"{w}x{h}_{img}"
        #     prInfo(f"UPDATING IMAGE NAME: [IPIMAGE{i:02d}.{IMF}] => [{newname}] in {stage} template")
        #     prompt_text = re.sub(f"\"image\": \"IPIMAGE{i:02d}.{IMF}\",", f"\"image\": \"{newname}\",", prompt_text)

    # bytesave_prompt(prompt_text,"test",config)
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
    str = ">>> "+Fore.LIGHTCYAN_EX+cmd+Fore.RESET
    print(str,flush=True)
    os.system(f'webExecute.py "{str}"')
def prInfo(info):
    """
    print Information
    """
    str = ">>> "+Fore.LIGHTMAGENTA_EX+info+Fore.RESET
    print(str,flush=True)
    os.system(f'webExecute.py "{str}"')
def prErr(err):
    """
    print Errors
    """
    str = ">>> "+Fore.RED+err+Fore.RESET
    print(str)
    os.system(f'webExecute.py "{str}"')

    str = ">>> "+Fore.RED+"Abort Flag Set"+Fore.RESET
    print(str,flush=True)
    os.system(f'webExecute.py "{str}"')

    traceback.print_stack()
    abort_flag(1)
    playsound("../error.wav")
    exit()
def prAnn(ann):
    """
    print Announcements
    """
    str = ">>> "+Fore.LIGHTCYAN_EX + ann + Fore.RESET
    print(str,flush=True)
    os.system(f'webExecute.py "{str}"')

def prSub(sub):
    """
    print Subsystem Output
    """
    str = Fore.LIGHTBLUE_EX + sub + Fore.RESET
    print(str,flush=True)
    os.system(f'webExecute.py "{str}"')

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
def increment_counter(config):
    sdir = f"{config['xsettings_dir']}"
    cval = 0
    cfile = f"{config['xsettings_dir']}/counter.json"
    if os.path.exists(cfile):
        cval = loadparam("counter",dir=sdir)
    cval +=1
    saveparam("counter",cval,dir=sdir)
    return cval

def procexit():
    abort_flag(1)
def saveparam(key,val,**kwargs):
    dir = tryit(kwargs,"dir","/tmp")
    with open(f'{dir}/{key}.json', 'w') as f:
        f.write(json.dumps(val))
def loadparam(key,**kwargs):
    dir = tryit(kwargs,"dir","/tmp")
    with open(f'{dir}/{key}.json', 'r') as f:
        val = json.load(f)
        return(val)

def upscale_f(outdir,config):
    files = get_sorted_files(f"{outdir}/*.{config['params']['imgfmt']}")
    ct = len(files)
    i = 1
    for file in files:
        cmd = f"./simple_upscale_image.sh {file} {config['params']['upscale']} {outdir}/upscaled"
        # prCmd(cmd)
        print(f"{i}/{ct}",end="\r")
        prunlive(cmd)
        i+=1
    print("\n")
def upscale_v(outdir,config):
    video = f"{outdir}/final.mp4"
    cmd = f"./simple_upscale_video.sh {video} {config['params']['upscale']} {outdir}/upscaled"
    prCmd(cmd)
    prunlive(cmd)
def wait_for_server():
    state = False
    while state != True:
        try:
            state = requests.head("http://127.0.0.1:8188/")
            # state = urllib.request.urlopen("http://127.0.0.1:8188/").getcode()
        except:
            pass
        prAnn(f"Waiting for http://127.0.0.1:8188/ - SERVER STATE: {state}")
        time.sleep(5)
        if f"{state}" == "<Response [200]>":
            state = True



