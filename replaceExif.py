#!/bin/env python
from os import fsencode
from pyexif import pyexif


import exiftool
import json
from pprint import pprint
file = "/tmp/x.pnghome/jw/src/ComfyUI/output/textract_00001.png"
wffile = "/home/jw/store/src/longanim/merge/masks_v0.json"


from pyexiv2 import Image

i = Image(file)
exif_dict = i.read_exif()
# i.read_iptc()
# i.read_xmp()
print(exif_dict)
for x in exif_dict:
    print(exif_dict[x])


# _dict = {"Workflow":"PNG:Prompt"}
# i.modify_exif(_dict)


