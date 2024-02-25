#!/bin/env python
import long_anim_lib as p
import os
import toml
import shutil
#!==================================================================================

os.chdir("/home/jw/store/src/longanim/merge")
with open(f"images/mergerun.toml", 'r') as f:  C = toml.load(f)
PROJECT = C['project']

stages = ["stage_1","stage_2","stage_3","stage_4",]
for stage in stages:
    if os.path.exists(f"{stage}/{PROJECT}"):
        if C[f'{stage}_clear'] == False:
            v = input(f"Existing stage_1/{PROJECT} exists...  Delete? (y/[n])")
            if v.upper() == "Y":
                shutil.rmtree(f"{stage}/{PROJECT}")
            else:
                p.prInfo(f"▓▓▓▓▓▓ Using existing files in [{stage}/{PROJECT}]")
        else:
            p.prInfo(f"▓▓▓▓▓▓ Deleting all files in [{stage}/{PROJECT}]")
            shutil.rmtree(f"{stage}/{PROJECT}")

