

# Instructions to create long-form video from multiple short clips.

## This process uses the following:

- FFmpeg with NVIDIA encoding enabled

- https://github.com/vladmandic/rife.git (for interpolation, required a special conda env, in my case)

- https://github.com/mpolinowski/Real-ESRGAN (for upscaling)

### Files and Folders

- A folder that will contain the settings used by ComfyUI (ex: `~/settings/ComfyUI`).  

- Each new animation settings will exist in a named subfolder in this directory. (ex: `~/settings/ComfyUI/myanim_01`)

- In each subfolder, there must exist the following:
  - A TOML file named "0_anim.toml' with the project settings.
    Two API-saved workflows, one for the *prep* stage called `1_prep_API.json` and one for the *anim* stage called `1_anim_API.json`.  There should also be non-API version, ()`1_anim.json`, `1_prep.json`).  These get saves to the output folder, which is important as the embedded workflows in the generated PNG files are useless for theComfyUI GUI, as API workflows are not supported by the GUI.
  - Any images (jpg, png only)  or videos (mp4 only) files that will be used as inputs.

This process requires a video.  The frames of that video are used as CN inputs.

Here is an example `anim.toml` file for an animation project called `spagvik`.

```bash
name    = "spagvik"

#version = "256"
#w       = 256
#h       = 144

version = "512"
w       = 512
h       = 288
#
#version = "960"
#w       = 960
#h       = 540

[loc]
# loacation of TOML, images, videos, etc.
settings_dir = "/home/jw/src/sdc/settings/COMFY/spagvik"

# get appended with 'version' => output_256
output_dir = "output_"
input_dir = "output_"


# Don;t use /tmp as the app wipes everything in this folder
tmpdir = "/fstmp"

[files]
# The length of the video and fps determines the length of the animation and number of groups
anim_template_name= "1_anim_API.json"
prep_template_name= "1_prep_API.json"

video =             "spaceclouds_hole2.mp4"
IP_images = [
            "viking",
#            "spagmon",
            "angel",
            ]

[specs]
# this must be a file spec that ONLY sees project related MP4s
# The app automatically numbers output clip files with  zero padded
# 5-digit numbers. This spec is prefixed by the project.name (above)
mp4_output_wc = "_?????.mp4"

[params]
debug     = true
groupsize = 48
interpx   = 20 # For transitions, NOT for FILM interpolation
overlap   = 0 # Don't use - deprecated
fps       = 8
maxloops  = 99  # max numner of loops (fgroups) limit to 99 due to file having 2-place digits, i.e., HED_00
steps     = 20
imgfmt    = "png"
start_at_fgroup = 0
max_extracted_frames = 0 # 0 = no limit, this is used only for CN preprocessing
runtime              = 300 # in seconds.  OVERIDES 'max_extracted_frames'. If not 0, calculates 'max_extracted_frames'
# 300 = 5 min
# 600 = 10 min
# 900 = 15 min

everynth             = "1/1" # extract 1 frame every 4 seconds = 1 frame every 8*4=32 frames (at 8 fps)
upscale              = 4 # 2 or 4 only



[prep]
# List all CNs used, and use the same names here as were used in the workflows (without the _ZZ or _00)
# Any CN listed here assumes there is already a collection of frames in the input folder

# cnets = ["HED","POSE","SEG","DEPTH"]
cnets = ["DEPTH"]
# cnets = ["HED"]
```


There are three stages.

- Preparation
- Animation
- Merging

## Preparation

The *prep* workflow requires:

- The **Save Image Extended** node, and in that node, the **filename_prefix** and **foldername_prefix** must be any name that is all caps, no spaces, followed by `"_ZZ"`
- The "Load Images" node "directory" field must be `<tmp_dir_name>/ZZ`
- The ControlNet Preprocessor can be set to any resolution as long as it matches the resolution defined in the animation workflow.  This value is only used as a token and is replaced with the resolution defined in the TOML file.
- The *prep* stage requires the file `1_prep_API.json` in the project setting folder.

The *prep* stage creates preprocessed ControlNet clips used by **ComfyUI-Video-Helper => Load Images** node, which are then fed into the **Apply ControlNet (Advanced)** node.   

To run the *prep* stage, issue the command:

```bash
./LONGANIM -P
```



The *prep* process reads the video assigned in the TOML file, extracts is to a temp folder at an FPS defined in the TOML file.

It then creates subgroups of the extracted frames, each with `groupsize` frames (defined in TOML).  A `groupsize` of 48 is max, as beyond that all movement to destroyed by Animatediff.

Each subgroup is processed, producing `groupsize` collections of images saved as numbered folders in the default ComfyUI input directory.

*Note: to make things less complicated, the output and input folders, as required by ComfyUI (and which are defined in the TOML file) are the same folder/*

Example of input folder preprocessed images for the **HED** ControlNet:

```text
./HED_00 
	HED_00_001.png 
	...
	HED_00_048.png
./HED_01 
	HED_01_001.png 
	...
	HED_01_048.png 
./mandala960x536.jpg

```

The *prep* loop submits prompts to the ComfyUI queue via WebSockets and waits for the queue to finish before it continues.

## Animation

The animation loop also processes each group of 48 frames by submitting them to the ComfyUI queue via WebSockets and waits for the queues to finish.  This is because there are cases where the following process might require input from the previous process.

*Note: Due to some memory issues, prob animatediff related, the ComfyUI server must be restarted for each iteration in the loop.  See the `START` shell script, which is called internally.  This script wipes the GPU memory, does some other stuff, and restarts the server, which has a hardcoded 20 second wait time for the server to come up.  Running on a different machine might require this time to be adjusted.*

The *anim* workflow requires:

- The file `1_amin_API.json` in the project setting folder.

- The **Load Images=>directory** field must be the same all-caps name used in the `prep` stage, but instead of being suffixed by `"_ZZ"`, it should be suffixed by `"_00"`.

- The output name for the video must be `"OUTPUTVIDEONAME"`. The actual output video is named "`final.mp4`".

The animation stage is initiated with the command:

```bash
./LONGANIM -A
```
The results are video files in the output folder:  

Note: The output folder is always appended by the whatever the `version` variable in the TOML file is, and must be the resolution of the WIDTH of the input/output files, i.e., 512, 256, 960, etc.

```text
output_512/spagvik
	spagvik_00001.mp4 
	spagvik_00001.png 
	spagvik_00002.mp4 
	spagvik_00002.png
```

*Note: If using frame prompts (0:"cat",10:"dog", etc), as there are only max 48 frames per clip (or whatever you set `groupsize` to be), the prompt can reference frames `0-<groupsize>`* 

### Output

Finished clips
```text
<settings_folder>/output_<version>/final.mp4
```

If upscaling is enabled:

```text
<settings_folder>/output_<version>/outv/final.mp4
```



## Merge

The merge stage extracts the above video and creates interpolated images between the last frame of the previous video and the first frame of the following video.  The number of interpolated frames created is determined by  `interpx` in the TOML file.

*Note: The interpolation is performed externally `simple_interp.sh`.  Upscaling is performed externally by `simply_upscale_video.sh` *

*merge* extracts all the videos, then inserts the interpolated frames, then reassembles the video to the final form, which is saved in the project output folder.

The merge stage is initiated with the command:

```bash
./LONGANIM -M
```
To run all three stages:

```bash
./LONGANIM -P -A -M
```

or better

```bash
clear && time unbuffer ./LONGANIM -P -A -M | tee run.log  
```

*Note:  'unbuffer' allows for ANSI codes to be sent to the screen while using 'tee'.*


### Bugs

- yes

  
