

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
# loacation of working dir.  the project name will be teh folder that will hold all 
# the TOML, images, videos, etc. If the project is named "boat", the folder will be <settings_dir>/<project>, i.e., "/home/jw/store/src/longanim/PROJECTS/boat")
settings_dir = "/home/jw/store/src/longanim/PROJECTS"

# gets appended with 'version' => output_256
output_dir = "output_"
input_dir = "output_"


# Don't use /tmp as the app wipes everything in this folder
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
- The *prep* stage requires the file `1_prep_API.json` in the project setting subfolder.
- **`LONGANIM` must be manually edit to change configs… it is not yet using the TOML file**

The *prep* stage creates preprocessed ControlNet clips used by **ComfyUI-Video-Helper => Load Images** node, which are then fed into the **Apply ControlNet (Advanced)** node.   

To run the *prep* stage, issue the command:

```bash
./LONGANIM -P
```
When run, the following vars are set:
```bash
# changes settings_dir location
settings_dir = /home/jw/store/src/longanim/PROJECTS/boat
output_dir = /home/jw/store/src/longanim/PROJECTS/boat/output_512
input_dir = /home/jw/store/src/longanim/PROJECTS/boat/output_512
# the file MUST be named as <x>x<y>_<anyname>.mp4, and <anyname> is set in the TOML file
INPUT VIDEO = /home/jw/store/src/longanim/PROJECTS/boat/512x512_ann.mp4
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

The animation loop also processes each group of 48 frames by submitting them to the ComfyUI queue via WebSockets and waits for the queues to finish.  ~~This is because there are cases where the following process might require input from the previous process.~~

*Note: Due to some memory issues, probably animatediff related, the ComfyUI server must be restarted for each iteration in the loop.  See the `START` shell script, which is called internally.  This script wipes the GPU memory, does some other stuff, and restarts the server, which has a hardcoded 20 second wait time for the server to come up.  Running on a different machine might require this time to be adjusted.*

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

*Note: The interpolation is performed externally `simple_interp.sh`.  Upscaling is performed externally by `simple_upscale_video.sh`* 

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

### Notes:

- 'unbuffer' allows for ANSI codes to be sent to the screen while using 'tee'.

  - On error, the file `/tmp/abort.flag` is created, which stops all further processing.  This file is delete when running `LONGANIM`.

  - Data is passed between processes with the JSON files ` /tmp/fgroups.json` and `/tmp/fgroups_ct.json`.  These are deleted when running `LONGANIM -P`
  - If running a new process using the same CN input files from a previous run, skip the `-P` argument of `LONGANIM`.


### Bugs

- yes

  

For more details, read comment in `0_anim.toml` and `long_anim_v4.py`.





# Latent Image Merging

This process is contained in the code in`longanim/merge` and is, for the most part, independent of the `longanim` process.

## Programs and Scripts

- **`qmask_v0.py`**

  - Creates interpolated frames

  - Uses:

    - **`masks_v0_API.json`** (created from **`masks_v0.json`**)

  - Args:

    ```bash
    -h, --help
    -o, --output_dir      	passed to the ComfyUI '--input_directory' arg
    -i, --input_dir       	passed to the ComfyUI '--output_directory' arg
    -p, --images
    -r, --res				Ex: '960:540', Default: '512:512'
    -t, --target_weight		maximum IPApapter weight.  Default: 1.0
    -c, --curve				linear|test|optimal.  Default: test
    ```

  - This is called in the **`MAKERUN`** script

- **`interpolate_v0.py`**

  - Uses:

    - **`interp_vo_API.json`** (created from **`interp_v0.json`**)

  - Args:

    - 

    - ```bash
      -h, --help				
      -o, --output_dir		passed to the ComfyUI '--input_directory' arg
      -i, --input_dir			passed to the ComfyUI '--output_directory' arg
      -n, --name				Project or session name
      -F, --frame_rate		Default: 8
      -M, --multiplier		Number of interpolated frames to create. Default:??
      -I, --image_load_cap	
      -J, --interpolate		Number of FILM frames to create.  Default: ??
      -L, --lastclip			(depricated)
      ```

## Files

- **`masks_v0_API_map.json`**

  - maps node names to IDs.  Used for updating values in **`qmask_v0.py`**a readable manner.  **THIS MUST BE MANUALLY SYNCED**

  - ```
    cnames = {
        'Empty_Latent_Image':'3',
        'Load_Image_1':'12',
        'Load_Image_2':'27',
        'Apply_IPAdapter_2':'50',
        'Apply_IPAdapter_1':'51',
        'Save_Image':'59',
    }
    ```

## Execution Path

- images/BATCH
  - MERGERUN
    - qmasks_v0.py
      - GPUMEMCLEAR
      - START
    - interpolate_v0.py (loops) 
      - GPUMEMCLEAR
      - START
    - wait_for_glob.py

### Example

```bash
# image/BATCH
../MERGERUN -f aliencity -t mushrooms -w 960 -h 540 -p story_1
../MERGERUN -f mushrooms -t ancienthands -w 960 -h 540 -p story_1

```
```bash
  ./qmasks_v0.py \
   --output_dir /home/jw/src/longanim/merge/stage_1/MyProject/aliencity_ancienthands \
   --input_dir /home/jw/src/longanim/merge/images \
   --images aliencity.png,ancienthands.png \
   --curve 'optimal' \
   --res 960:540 &
```
```bash
./interpolate_v0.py 
--name MyProject \
--input_dir stage_1/MyProject/aliencity_ancienthands/ \
--output_dir stage_2/MyProject/aliencity_ancienthands/ \
--frame_rate 8 \
--multiplier 2 \
--image_load_cap 1000 \
--interpolate 1
```





Notes:

- When starting the server, optionally define the input/output folders
```bash
~/src/longanim/START  \
-i /home/jw/store/src/longanim/PROJECTS/boat/output_512 \ 
-o /home/jw/store/src/longanim/PROJECTS/boat/output_512
```

- All image names must be zero-padded 2-digit names (01.png, 02.png,…,99.png) which is teh order that they are processed
- A project folder, which contain the TOML, JSON, images, batch file, etc, can me anywhere, but MUST be symlinked to a folder named “IMAGES” in the folder where `mergerun,py`, `qmask_v0.py`, and `interpolate_v0,py` exist.

- The project asset folder IMAGES contains:
  - `mergerun.toml`
  - `BATCH`
    - This is created with `../make_mergerun_batch.py  > BATCH` from within the IMAGES folder.
  - `??.png` image files
  - `qmasks_v0.json`, `qmasks_v0_API.json`
  - `interp_v0.json`, `interp_v0_API.json`
  - `LOCAL_START`
    - This starts the ComfyUI server using the projects input/output folders





# WORKFLOW RULES

## colors

- Setters: red
- Getters: green
- Blocks: yellow
- Bus: black
- Comments: blue
- UE: purple
- Logic: cyan 

## shapes

- Default: rounded
- Prompts: square
- Bus: square
- Comments: square

## Groups

- Default: light blue

- subfunctions: green

- Commants: black

  

# PROCESS

- Move to workign root folder:
```bash
cd ~/src/longanim/PROJECTS/sphere
```
- **`ytgrab`** video  vname
- Extract audio with:
```bash
ffmpeg -i ~/Videos/v_name.mp4 -vn -ar 44100 -ac 2 -ab 192k -f wav ~/Videos/v_name.wav
```

- open **`~/Videos/v_name.mp4`** in Resolve.  

- Edit and save as MOV as **`~/Videos/name_1920x1080.mov`**

- Convert to MP4 with:
```bash
HandBrakeCLI -i ~/Videos/v_name.mov -o ~/Videos/v_name_1920x1080.mp4  -e nvenc_h265
```

- Resize with:
```bash
ffmpeg -i ~/Videos/name_1920x1080.mp4  -c:v libx264 -t 15 -pix_fmt yuv420p -vf scale=486:864 ~/Videos/name_486x864.mp4 
```

- Extract frames with:  (needed for making controlnets?)
```bash
mkdir /xfstmp/name_486x864_8fps

ffmpeg -y -loglevel warning -i ~/Videos/name_486x864.mp4  -r 8/1 /xfstmp/name_486x864_8fps/%04d.png

#Either check "Load_Video::force_rate=8" or change the src rate to match FPS as well
ffmpeg -y -loglevel warning -hwaccel cuda  -i ~/Videos/name_486x864.mp4 -crf 20 -vf "minterpolate=fps=8:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1" input_486/name_486x864_8fps.mp4

```

## Start ComfyUI

- Make input/output dirs if necessary.
- Start Comfy with **`./486x864_LOCAL_START`**.

- Create necessary workflows

```bash
cp ASSETS/UTIL_MAKE_CN.json 486x864_swing_MAKE_CN.json
cp 540x960_dubstep_MAKE_HUMAN_MASK.json 486x864_swing_MAKE_HUMAN_MASK.json
cp 540x960_dubstep_MAKE_VIDEO.json 486x864_swing_MAKE_VIDEO.json
```
## Make Controlnets

Load and edit **`486x864_name_MAKE_CN.json`** edit accordingly *(looks in **`/xfstmp`** folder for video)*

- Check update **`Rate`**, **`Subject`**, **`Width`**, **`Height`** at least.
- Submit query

- Move output files to input dir, and copy video source to input dir.
```bash
mv output_486/celine_486x864_8fps_POSE_ZZ.mp4 input_486  #file
mv output_486/celine_486x864_8fps_POSE_ZZ input_486  #folder
```
## Make Human Mask

- cope original video to inout folder:

```bash
cp ~/Videos/name_486x864.mp4  input_486 # needs to be in input_dir for masking
```
Edit **`486x864_name_MAKE_HUMAN_MASK.json`** accordingly

- Check update **`Frame Rate`** update **`Load_Video::video`** amd **`VideoCombine::filename`** field at least.
- Submit query

Save prefix as  **`name_HUMAN_MASK_486x864`**

- This create two files in the output folder, 
- **`swing_HUMAN_MASK_486x864_00001.mp4`**
- **`swing_HUMAN_MASK_486x864_00001-audio.mp4`** 
- Remove the **`00001`** parts and move just the video file (no sound) them both to the input folder

```bash
cd output_486
rename _00001 '' *
mv celine_HUMAN_MASK_486x864_8fps.mp4 ../input_486
cd ..
```

# Fixing Bad Masks

If the generated masks suck, create a mask with RunwayML, download it and save it as 
the orioginal name used previouslu, **`~/Videos/name_486x864.mp4`** and rerun the CN workflow.

The copy that same file to the inpout folded, but with tha adeed “_8fps” (makign sure teh video IS 8 fps of the “force rate is on”)  or reinterpolate the video 

```bash
cp  ~/Videos/name_486x864.mp4  input_486/name_486x864_8fps.mp4

or 

ffmpeg -y -loglevel warning -hwaccel cuda  -i ~/Videos/name_486x864.mp4 -crf 20 -vf "minterpolate=fps=8:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1" input_486/name_486x864_8fps.mp4
```

Remerber to copy ove rthe files from outout to infut folder



## Make Video

- Load and edit **`name_MAKE_VIDEO.json`** accordingly.
  - Load new mask file.
  - Load new CN file.
  - Check **`DIMS`**, **`FRAME RATE`**, **`TEXTPROMPT`**, **`BATCH_SIZE`**, **`TITLE`**, at least.
  - Copy over any necessary images to the input folder
  - If using IP MORPH or IP STACK:
    - Style the character with two 486x864 images in the input folder
    - 
    Submit query.





# OpenToonz processing

### Set vars

```bash
export OTVID="/home/jw/Desktop/wimg.mp4"
export INPUTDIR="/home/jw/src/longanim/PROJECTS/waterboy/input_512"
export POSEDIR="hl_486x864_8fps_POSE_ZZ"
```



### ~~To scale scale down from default 1920x1080  ONLY IF necessary~~

```bash
# scale for 512x512
ffmpeg -y -loglevel warning -i ${OTVID} -filter:v scale=-1:512 -c:a copy /fstmp/s1scale.mp4
# and crop
ffmpeg -y -loglevel warning -i /fstmp/s1scale.mp4 -vf "crop=512:512:0:0" /fstmp/s1cropped.mp4

#If no scalign needed, just copy
cp ${OTVID} /fstmp/s1cropped.mp4

####
# for single image
ffmpeg -y -loglevel warning -i ${OTVID} -r 8/1 ${INPUTDIR}/pose_%04d.png

# OR  for video
#clean first
333

# for simgle image
mogrify -channel RGB -negate ${INPUTDIR}/${POSEDIR}/pose_0001.png 


333
# !! ONLY IF NECESSARY... add this for 486x864
mogrify -resize 486x864 -background black -gravity center -extent 486x864 ${INPUTDIR}/${POSEDIR}/pose*.png

333
# clean target dir
rm -rf /xfstmp/hl_486x864_8fps/*  2>&1 > /dev/null
# cp tp /xfstmp if necessary (for making new CNs, such as DENSEPOSE)
cp ${INPUTDIR}/${POSEDIR}/*.png /xfstmp/hl_486x864_8fps
```
### Extract start here

```bash
export SCENE="aniani"
export DIMS="486x864_8fps"
export PROJECT="aniani"
export POSEDIR="aniani_486x864_8fps_POSE_ZZ"

# clean target dir

/bin/rm -rf /home/jw/src/longanim/PROJECTS/${PROJECT}/input/${SCENE}_${DIMS}_POSE_ZZ/*  2>&1 > /dev/null

# extract to folder |input|
ffmpeg -y -loglevel warning -i /home/jw/Desktop/${SCENE}.mp4 -r 8/1 /home/jw/src/longanim/PROJECTS/${SCENE}/input/${SCENE}_${DIMS}_POSE_ZZ/pose_%04d.png

# invert
mogrify -channel RGB -negate /home/jw/src/longanim/PROJECTS/${SCENE}/input/${SCENE}_${DIMS}_POSE_ZZ/pose*.png

# create new video of frames to |input|
ffmpeg -y -loglevel warning \
	-framerate 8 \
	-pattern_type glob -i "/home/jw/src/longanim/PROJECTS/${SCENE}/input/${SCENE}_${DIMS}_POSE_ZZ/pose*.png" \
	-c:v libx264 \
	-pix_fmt yuv420p \
	/home/jw/src/longanim/PROJECTS/${SCENE}/input/${SCENE}_${DIMS}_POSE_ZZ.mp4

# npw exists 
# 	=> /home/jw/src/longanim/PROJECTS/aniani/input/aniani_486x864_8fps_POSE_ZZ
# 	=> /home/jw/src/longanim/PROJECTS/aniani/input/aniani_486x864_8fps_POSE_ZZ.mp4

# NEXT: run "MAKE_BLUR_MASK_FROM_POSE.json"
```

# Conda for comfyui (CUDA 11.8 & 12.1)

from link https://www.reddit.com/r/comfyui/comments/17abmwp/comfyui_needs_cuda_121/

Tensorflow fpr pip  https://www.tensorflow.org/install/pip



- NVIDIA® GPU drivers version 450.80.02 or higher. (https://www.nvidia.com/download/index.aspx?lang=en-us)
  - (Debian 12)  This downloads a .run file, but when running it, it complains that the driver have already been instatted, and also suggests using the .deb package instead.  I assume it is referring to one of the two following .deb install

- CUDA® Toolkit 11.8.  (https://developer.nvidia.com/cuda-toolkit-archive)
```bash
# Debian 12
wget https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda-repo-debian11-11-8-local_11.8.0-520.61.05-1_amd64.deb
sudo dpkg -i cuda-repo-debian11-11-8-local_11.8.0-520.61.05-1_amd64.deb
sudo cp /var/cuda-repo-debian11-11-8-local/cuda-*-keyring.gpg /usr/share/keyrings/
sudo add-apt-repository contrib
sudo apt-get update
sudo apt-get -y install cuda

export PATH="/usr/local/cuda-11.8/bin:$PATH"
export LD_LIBRARY_PATH="/usr/local/cuda-11.8/lib64:$LD_LIBRARY_PATH"
```


- cuDNN SDK 8.6.0. (https://developer.nvidia.com/cudnn)
```bash
# Debian 12
wget https://developer.download.nvidia.com/compute/cudnn/9.0.0/local_installers/cudnn-local-repo-debian11-9.0.0_1.0-1_amd64.deb
sudo dpkg -i cudnn-local-repo-debian11-9.0.0_1.0-1_amd64.deb
sudo cp /var/cuda-repo-debian11-9-0-local/cudnn-*-keyring.gpg /usr/share/keyrings/
sudo add-apt-repository contrib
sudo apt-get update
sudo apt-get -y install cudnn
# To install for CUDA 11, install the CUDA 11 specific package:
sudo apt-get -y install cudnn-cuda-11
# To install for CUDA 12, install the CUDA 12 specific package:
sudo apt-get -y install cudnn-cuda-12
```


- TensorRT (https://docs.nvidia.com/deeplearning/tensorrt/archives/index.html#trt_7)

~~Download CUDA 11.8 from Arch Archive:  https://archive.archlinux.org/packages/c/cuda/cuda-11.8.0-1-x86_64.pkg.tar.zs~~

Step by step instruction how to install CUDA 11 Ubuntu 20.04

- https://gist.github.com/ksopyla/bf74e8ce2683460d8de6e0dc389fc7f5

```
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/usr/local/cuda/lib64:/usr/local/cuda/extras/CUPTI/lib64"
export CUDA_HOME=/usr/local/cuda
export PATH="/usr/local/cuda/bin:$PATH"
```





Check system CUDA installed: 

```bash
# Arch
pacman -Q|grep cuda
pip list|grep -i cuda

# Debian
apt list --installed|grep -i cuda
```



pip list|grep -i cuda


```bash
conda create --name comfy
conda activate comfy
conda update -n base -c conda-forge conda
conda config --append channels nvidia
conda config --append channels conda-forge
conda config --append channels defaults
conda config --append channels anaconda
conda install pip

pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
#pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

cd ~/src/ComfyUI

python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
python -m pip install h5py
python -m pip install impact
python -m pip install opencv-python 
python -m pip install evalidate 
python -m pip install numba 
python -m pip install numexpr 
python -m pip install addict 
python -m pip install segment_anything 
python -m pip install git.remote  # still can't be found
python -m pip install piexif 
python -m pip install realesrgan 
python -m pip install pandas 
python -m pip install simpleeval 
python -m pip install yapf 
python -m pip install scikit-image  # was skimage
python -m pip install clip
python -m pip install smplx
python -m pip install trimesh
python -m pip install pyrender
python -m pip install shapely
python -m pip install onnxruntime
python -m pip install onnxruntime-gpu
python -m pip install PyOpenGL-accelerate
python -m pip install moviepy
python -m pip install gray2color
python -m pip install kornia

cd ~/src/ComfyUI/custom_nodes
git clone https://github.com/ltdrdata/ComfyUI-Manager.git



```

Also, read **`  /home/jw/src/ComfyUI/custom_nodes/comfy_mtb/INSTALL.nd`** to install node **`comfy_mtb`**.

Additionally:
```
apt-get install ffmpeg-python  
```
or
```
yay -S ffmpeg-python
```




## Issues

  - Running org CUI
    
    - ‘ffmpeg_bin_path’ is not set
    
      - ```bash
        export ffmpeg_bin_path="/bin/ffmpeg"
        ```
    
      - export ffmpeg_bin_path="/bin/ffmpeg"
    
    - ModuleNotFoundError: No module named 'torchvision.transforms.functional_tensor'
    
      - torchvision already installked
      - ```bash
        joe ~/.conda/envs/comfy/lib/python3.12/site-packages/basicsr/data/degradations.py
        ```
        change
        `from torchvision.transforms.functional_tensor import rgb_to_grayscale`
        to
        `from torchvision.transforms.functional import rgb_to_grayscale`
        
      - see https://github.com/AUTOMATIC1111/stable-diffusion-webui/issues/13985
    
    
    Additionally, the following need to be installed
    
    ```
    pip install ffmpeg-python
    
    ```
    
    


# ComfyUI Installer (CUDA 12.1)

- check out -> https://github.com/HAMM3REXTREME/ComfyUI-Installer
- run `/home/jw/store/sd_models_repo/comfy_links.sh`
- Install Manager
```
cd /home/jw/store/src/ComfyUI-Installer/ComfyUI/custom_nodes
git clone https://github.com/ltdrdata/ComfyUI-Manager.git
```
- Install missing nodes with Manager
- Install https://github.com/diffus3/ComfyUI-extensions

```bash
git clone https://github.com/diffus3/ComfyUI-extensions /home/jw/store/src/ComfyUI-Installer/ComfyUI//web/extensions/diffus3
```

- Copy over all the other models, i.e.:

```
cp /home/jw/store/src/ComfyUI/custom_nodes/ComfyUI-AnimateDiff-Evolved/models/* /home/jw/store/src/ComfyUI-Installer/ComfyUI/custom_nodes/ComfyUI-AnimateDiff-Evolved/models
```

## Issues

- ModuleNotFoundError: No module named 'inference_core_nodes'

- ```
  export PYTHONPATH=/home/jw/src/ComfyUI-Installer/ComfyUI/custom_nodes/ComfyUI-Inference-Core-Nodes/src:$PYTHONPATH
  ```

  -  Problems:
     ! No module named 'custom_nodes.ComfyUI_ADV_CLIP_emb'



# Docker

https://gitlab.com/highstaker/comfyui-docker/-/blob/master/README.md?ref_type=heads

 yay -S libelf

 yay -S nvidia-container-toolkit




```


```



"0" :"A dog dressed as a Scottish Highlander",
"25" :"An ape dressed as a Roman Centurion",
"38":"A cat dressed as a ballet dancer"

```


"0" : "A 1960s girl in a white dress with red polkadots dancing to rock and roll",
"25": "A japanese Sumo wrestler",
"38": "A viking shaman"


"0" : "A sexy 1960s girl in a white dress with red polka dots dancing to rock and roll",
"25": "A Viking shaman"

"0" : "A sexy 1960s girl in a white dress with red polka dots dancing to rock and roll",
"1": "A Viking shaman",
"2": "A Viking shaman",
"3": "A Viking shaman",
"4": "A Viking shaman",
"5": "A Viking shaman",
"6": "A Viking shaman",
"7": "A Viking shaman",
"0" : "A sexy 1960s girl in a white dress with red polka dots dancing to rock and roll",
"1": "A Viking shaman",
"2": "A Viking shaman",
"3": "A Viking shaman",
"4": "A Viking shaman",
"5": "A Viking shaman",
"6": "A Viking shaman",
"48": "A Viking shaman"


"0":"A dog standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed",
"4":"A dog standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed",
"8":"A dog standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed",
"24":"A German Shepard",
"40":"A dog standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed",
"44":"A dog standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed",
"48":"A dog standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed"


"0": "A dog standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed",
"4": "A dog standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed",
"8": "A dog standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed",
"24": "German Shepar dog",
"38": "A dog standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed",
"42": "A dog standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed",
"48": "A dog standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed"


"0":"A wolf standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed",
"4":"A wolf standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed",
"8":"A wolf standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed",
"24":"A Chihuahua",
"40":"A wolf standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed",
"44":"A wolf standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed",
"48":"A wolf standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed"

"0":"A Chihuahua standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed",
"4":"A Chihuahua standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed",
"8":"A Chihuahua standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed",
"24":"A wolf",
"40":"A Chihuahua standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed",
"44":"A Chihuahua standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed",
"48":"A Chihuahua standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed"

#1

"0": "German Shepard standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed",
"4": "A fire-breathing lizard dragon standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed",
"8": "A fire-breathing lizard dragon standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed",
"24": "A white French poodle",
"40": "A Chihuahua standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed",
"44":"A Chihuahua standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed",
"48":"A Chihuahua standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed"

#2
"0": "A Chihuahua standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed",
"4": "A Chihuahua standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed",
"8": "A Chihuahua standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed",
"24": "A Fennec fox",
"40": "A wolf standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed",
"44": "A wolf standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed",
"48": "A wolf standing upright with outstretched arms. 8k, UHD, hyperrealistic photograph, highly detailed"



```
