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


# file = "PROJECTS/sphere/workflow.json"
file = False
argv = sys.argv[1:]
try:
    opts, args = getopt.getopt(
        argv, "hf:",
        [   'help',
                    'file=',
                ],
    )
except Exception as e:
    print(str(e))


for opt, arg in opts:
    # if opt in ("-h", "--help"):p.showhelp()
    if opt in ("-f", "--file"):file = arg
    if opt in ("-x", "--execute"):execute = True

import re




#TEST
"""
str = 'FILENAME: [xxx]\n<hr>outputs: <var>.mp4\n\n<br>\n \n###### DESC:\n\n<br>\n \n###### LOCATION:\n## /home/jw/store/src/longanim/PROJECTS/boat/\n\n<br>\n\n###### REFERENCES:\n- Attention Masking with IPAdapter and ComfyUI\n- https://www.youtube.com/watch?v=vqG1VXKteQg</var>"'

p.prCmd(str)
# str = re.sub(r"/(.*)(FILENAME:.*\])(.*)/",rf"\1FILENAME: [{file}]\2", str)
str = re.sub(search,replace, str)

p.prInfo(str)

exit()
"""
try:
    with open(file) as f:
        prompt_obj = json.load(f)
except Exception as e:
    print(Fore.RED + f"{file:40s}" + Fore.LIGHTRED_EX + "CORRUPTED!!" + Fore.RESET)
    print(e)
    exit()

search = r"FILENAME:.*\[.*\]"
replace = rf"FILENAME: [{file}]"

for els in prompt_obj['nodes']:
    if els['type'] == "Note" or els['type'] == "Note Plus (mtb)":
        lines = els['widgets_values']
        for i in range(len(lines)):
            fnd = lines[i].find("FILENAME:")
            if fnd != -1:
                newstr = re.sub(search, replace, lines[i])
                # print(f"\tSRC:[{file}|")
                # print("\tORG:|"+Fore.WHITE+ f"{str.encode(lines[i])}|" + Fore.RESET)
                # print("\tNEW:|"+Fore.LIGHTWHITE_EX + f"{str.encode(newstr)}|" + Fore.RESET)
                if lines[i] == newstr:
                    #! line is unchanged
                    if newstr.find("[") == -1:
                        #! NODE found, but not  not '['
                        print(Fore.MAGENTA+f"{file:40s}"+Fore.LIGHTMAGENTA_EX+"Probably improper formatting ('[')"+Fore.RESET)
                    else:
                        #! NODE found, '[' found, but lines unchanged
                        # print(Fore.YELLOW+f"{file:40s}"+Fore.LIGHTYELLOW_EX+"Already Updated"+Fore.RESET)
                        pass
                else:
                    # ! line has changed
                    print(Fore.GREEN + f"{file:40s}" + Fore.LIGHTGREEN_EX + "Line Updated" + Fore.RESET)
                    lines[i] = newstr
                    testfile = "/tmp/test.json"
                    #! save and reload
                    with open(testfile, "w") as f:
                        json.dump(prompt_obj, f, indent=4)

                    try:
                        with open(testfile, "r") as f:
                            prompt_obj = json.load(f)
                        #! it's OK, so save
                        with open(file, "w") as f:
                            json.dump(prompt_obj, f, indent=4)

                    except Exception as e:
                        print(Fore.RED + f"{file:40s}" + Fore.LIGHTRED_EX + "CORRUPTED!!" + Fore.RESET)
                        exit()

