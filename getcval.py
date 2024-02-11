#!/bin/env python
import toml
import os, sys, getopt


def showhelp():
    print("help")
    rs = """
    -h, --help          show help
    -c, --cfile         dir only, "anim.toml" is assumed
    -k, --key           ex "name", "loc.tmpfile"
    """
    print(rs)
    exit()

argv = sys.argv[1:]

try:
    opts, args = getopt.getopt(
        argv,
        "hc:k:",
                [   'help',
                    'cfile=',
                    'key=',
            ],
    )
except Exception as e:
    print(str(e))

key = False
cfile = False #"/home/jw/src/sdc/settings/COMFY/spagvik/anim.toml"
for opt, arg in opts:
    if opt in ("-h", "--help"):showhelp()
    if opt in ("-c", "--cfile"):cfile = f"{arg}/0_anim.toml"
    if opt in ("-k", "--key"):key = arg



#! from TOML
with open(cfile, 'r') as f:  config = toml.load(f)

ks = key.split(".")
if len(ks) == 1:
    val = config[ks[0]]
else:
    val=config[ks[0]][ks[1]]

print(val)

# print(config['name'])
