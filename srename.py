#!/bin/env python
import cv2
import sys, os
import long_anim_lib as p
import re
fn = sys.argv[1]


im = cv2.imread(fn)
dims = list(im.shape)
dstr = f"{dims[0]}x{dims[1]}x{dims[2]}"

fp = p.split_path(fn)
        # "dirname": dirname,
        # "basename": basename,
        # "ext": ext,
        # "nameonly": nameonly,
        # "fullpath": fullpath,


newname = re.sub("_[0-9]{3,4}x[0-9]{3,4}x[0-9]","",fp['nameonly'])

# print(">>>",newname)

cmd = f"mv {fp['dirname']}/{fp['nameonly']}.{fp['ext']}  {fp['dirname']}/{newname}_{dstr}.{fp['ext']} "
print(cmd)
os.system(cmd)
