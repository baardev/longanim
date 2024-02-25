#!/bin/env python
import json
import long_anim_lib as p
from pathlib import Path
from itertools import count, takewhile
import os
import sys
import getopt
from pprint import pprint
import toml
from colorama import init, Fore
import time
from sklearn.preprocessing import minmax_scale
#! ex:  xdata = minmax_scale(data, feature_range=(0, 10), axis=0, copy=True)

def showval(prompt,key):
    found = p.find_in_json(prompt, key)
    for f in found:
        p.prInfo("\t" + f)
def frange(start, stop, step):
    tnary = []
    nary = takewhile(lambda x: x < stop, count(start, step))
    for i in list(nary):
        tnary.append(round(i,2))
    # print(tnary)
    return tnary
def setval(prompt,idx,key,val,**kwargs):
    verbose = p.tryit(kwargs,"verbose",False)

    p.prInfo(f"\t['{idx}']['inputs']['{key}'] = {val} ({type(val)})")
    try:
        prompt[idx]['inputs'][key] = val
        return prompt
    except Exception as e:
        print(Fore.GREEN)
        pprint(sys.argv)
        print(Fore.RESET)

        print(Fore.RED)
        print(json.dumps(prompt,indent=4))
        print(Fore.RESET)

        print(Fore.YELLOW)
        print(f"ERROR: [{e}")
        print(f"SETTING:  |{key}| => |{val}|")
        print(f"TYPE: {type(e).__name__}")
        print("Existing keyvals:")
        showval(prompt,key)
        print(Fore.RESET)

        exit()


#!==================================================================================
with open(f"IMAGES/mergerun.toml", 'r') as f:  C = toml.load(f)
p.prAnn("┌─────────────────────────────────────────────")
p.prAnn("│ ENTERED 'qmasks_v0.py'")
p.prAnn("└─────────────────────────────────────────────")

argv = sys.argv[1:]
opts = False
image_01 = False
image_02 = False
curve = "test"
try:
    opts, args = getopt.getopt(
        argv, "ho:i:p:r:t:c:",
        [   'help',
                    'output_dir=',
                    'input_dir=',
                    'images=',
                    'res=',
                    'target_weight=',
                    'curve=',
            ],
    )
except Exception as e:
    print(str(e))

output_dir = False
input_dir = False
res = "512:512"
width = 512
height = 512
target_weight = 1.0

for opt, arg in opts:
    if opt in ("-h", "--help"):p.showhelp()
    if opt in ("-o", "--output_dir"):output_dir = arg
    if opt in ("-i", "--input_dir"):input_dir = arg
    if opt in ("-r", "--res"):
        res = arg
        parts = str(arg).split(":")
        width = parts[0]
        height = parts[1]
    if opt in ("-p", "--images"):
        itmp = str(arg).split(",")
        image_01 = itmp[0]
        image_02 = itmp[1]
    if opt in ("-t", "--target_weight"):target_weight = float(arg)
    if opt in ("-c", "--curve"):curve = arg

p.prInfo(f"INPUT: [{input_dir}]")
p.prInfo(f"OUTPUT: [{output_dir}]")
p.prInfo(f"IMG 1: [{image_01}]")
p.prInfo(f"IMG 2: [{image_02}]")
p.prInfo(f"CURVE: [{curve}]")

if image_01 == False or image_02 == False:
    p.prErr("Missing one or both image names")
if output_dir == False or input_dir == False:
    p.prErr("Missing one or both in/output dirs")

istub1 = image_01.replace(".png","")
istub2 = image_02.replace(".png","")
#! output from the START command

if os.path.isfile("/tmp/STARTED"):
    pass
else:
    hideSTDOUT = "2>&1 >> /tmp/START.log"
    p.prAnn(f"Killing server in {__file__}")
    p.killproc("main.py")
    if output_dir != False:
        cmd = f"~/src/longanim/START -i {input_dir} -o {output_dir} {hideSTDOUT} &"
    else:
        p.cleandir(output_dir)
        cmd = f"./START {hideSTDOUT} &"

    p.prAnn(f"Restarting server in {__file__}")
    p.prCmd(cmd)
    os.system(cmd)

    start = time.time()
    p.wait_for_server()
    end = time.time()
    p.prInfo(f"Total wait time for server: {end - start}")

    os.system("touch /tmp/STARTED")

with open(f"IMAGES/{C['qmasks_workflow']}") as f:
    prompt = json.load(f)



i1 = 0.0
i2 = 1.0
c = 0

curves = {
    'test': [0,0.25,0.50,0.75,1],
    'optimal': [0,0.03,0.06,0.09,0.12,0.15,0.18,0.21,0.23,0.25,0.27,0.29,0.31,0.33,0.35,0.37,0.39,0.41,0.42,0.43,0.44,0.45,0.46,0.47,0.48,0.49,0.5,0.51,0.52,0.53,0.54,0.55,0.56,0.57,0.58,0.59,0.6,0.62,0.64,0.66,0.68,0.7,0.72,0.74,0.76,0.78,0.81,0.84,0.87,0.9,0.93,0.96,0.99,1],
    'linear': [],
}
#! make linear curve
for i in frange(0,1.01,0.01): curves['linear'].append(i)

#! NOTE: is the last file is not  named "*_1.00-0.00_00001_.png" then tehg 'waitinf_for_glob.py" will not work and must be changed

cnames = {
    '2_CheckpointLoaderSimple': '2',
    '3_EmptyLatentImage': '3',
    '4_CLIPTextEncode': '4',
    '5_CLIPTextEncode': '5',
    '6_VAEDecode': '6',
    '10_IPAdapterModelLoader': '10',
    '11_CLIPVisionLoader': '11',
    '12_LoadImage': '12',
    '13_PrepImageForClipVision': '13',
    '27_LoadImage': '27',
    '50_IPAdapterApply': '50',
    '51_IPAdapterApply': '51',
    '52_PrepImageForClipVision': '52',
    '59_SaveImage': '59',
    '80_LoadImageMask': '80',
    '81_KSamplerAdvEff': '81',
    '83_HighRes-Fix Script': '83',
    # '86_IPAdapterModelLoader': '86',
    # '87_CLIPVisionLoader': '87',
    # '88_LoadImageMask': '88',
    # '91_CheckpointLoaderSimple': '91',
    # '93_HighRes-Fix Script': '93',
    # '94_EmptyLatentImage': '94',
    # '96_HighRes-Fix Script': '96',
    # '97_HighRes-Fix Script': '97',

}


applied_curve = curves[curve]

noisecurve = p.cycle(applied_curve)
cidx = 0
for j in applied_curve:
    i = j*target_weight
    c = c + 1
    ni1 = round(i1+i,2)
    ni2 = round(i2-ni1,2)
    prefix = f"{c:04d}_{ni1:3.02f}-{ni2:3.02f}"
    p.prInfo(f"PREFIX FILENAME => |{c:04d}_{prefix}|")


    p.prAnn("UPDATED VALUES:")
    setvalVerbose = C['verbose']

    prompt = setval(prompt,cnames['3_EmptyLatentImage'],"width",width,verbose = setvalVerbose) #3
    prompt = setval(prompt,cnames['3_EmptyLatentImage'],"height",height,verbose = setvalVerbose) # 3
    prompt = setval(prompt,cnames['12_LoadImage'],"image",f"{image_01}",verbose = setvalVerbose) # 12
    prompt = setval(prompt,cnames['27_LoadImage'],"image",f"{image_02}",verbose = setvalVerbose) # 27
    prompt = setval(prompt, cnames['50_IPAdapterApply'], "weight", str(ni1), verbose=setvalVerbose)  # 50
    prompt = setval(prompt, cnames['50_IPAdapterApply'], "noise", noisecurve[cidx]**C['image_2_noise'], verbose=setvalVerbose)  # 50

    prompt = setval(prompt,cnames['51_IPAdapterApply'],"weight",str(ni2),verbose = setvalVerbose) # 51
    prompt = setval(prompt, cnames['51_IPAdapterApply'], "noise", noisecurve[cidx]*C['image_1_noise'], verbose=setvalVerbose)  # 50

    prompt = setval(prompt,cnames['59_SaveImage'],"filename_prefix",prefix,verbose = setvalVerbose) # 59
    prompt = setval(prompt,cnames['80_LoadImageMask'],"image",C['mask_0'],verbose = setvalVerbose)  # 80

    prompt = setval(prompt,cnames['81_KSamplerAdvEff'],"add_noise",C['knoise'],verbose = setvalVerbose)  # 80



    # prompt = setval(prompt, cnames['88_LoadImageMask'], "image", C['mask_1'],verbose = setvalVerbose)  # 80

    try:
        p1key = "i"+istub1
        p1 = C[p1key]
        # p.prInfo(f"Loading CLIPtext var |{p1key}|': {p1}")

        p2key = "i"+istub2
        p2 = C[p2key]
        # p.prInfo(f"Loading CLIPtext var |{p2key}|': {p2}")

        cliptext = f"{p1} AND {p2}"

        prompt = setval(prompt, cnames['5_CLIPTextEncode'], "text", cliptext,verbose = setvalVerbose)  # 80
    except:
        pass
    #! submit prompt
    p.save_prompt(prompt,location=f"/tmp/saved_prompt_{C['project']}-{istub1}-{istub2}_API.json")
    p.prAnn(f"Saved Prompt: /tmp/saved_prompt_{C['project']}-{istub1}-{istub2}_API.json")
    prompt_id = p.queue_prompt(prompt)['prompt_id']

    p.prSub("CURRENT VALUES:")
    showval(prompt,"weight")
    showval(prompt,"image")
    # showval(prompt,"weight_type")
    # showval(prompt,"width")
    # showval(prompt,"height")
    cidx +=1

# p.prAnn("CURRENT VALUES:")
# showval(prompt,"weight")
# showval(prompt,"image")
# showval(prompt,"weight_type")
# showval(prompt,"width")
# showval(prompt,"height")
p.prInfo("┌─────────────────────────────────────────────")
p.prInfo("│ EXITING 'qmasks_v0.py'")
p.prInfo("└─────────────────────────────────────────────")


