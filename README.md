

# Instructions to create long-form video from multiple short clips.

## For the technique to work the following is required.

- FFmpeg

- https://github.com/vladmandic/rife.git

- A folder there will contain the settings used by ComfyUI.  Each new animation settings will exist in a named subfolder in this directory.

- In each subfolder, there must exist the following:
  - A TOML file named "anim.toml' with the project settings.
    Two API-saved workflows, one for the *prep* stage called `prep_API.json` and one for the *anim* stage called `anim_API.json`.
  - Any images (jpg, png)  or videos (mp4) files that will be used as inputs.

base files:
video (encvoded to the correct FPS.  Default is 8)
IP images
  
  
  
- The *prep* workflow requires 
  - The "Save Image Extended" node, and in that node, the 'filename_prefix' and foldername_prefix' must be any name that is all caps, no spaces, followed by `_ZZ`
  - The "Load Images" node "directory" field must be `<tmp_dir_name>/ZZ`
  - The ControlNet Preprocessor must be set to a resolution that is the same as the final output (this will be automated at some point)

Here is an example `anim.toml` file for an animation project called `ttest`.

```bash
[project]
name = "ttest"

[loc]
settings_dir = "/home/jw/src/sdc/settings/COMFY"
output_dir = "/home/jw/src/ComfyUI/output"
input_dir = "/home/jw/src/ComfyUI/input"
tmpdir = "/fstmp"

[files]
video = "src_960x540.mp4"
anim_template_name = "anim_API.json"
prep_template_name = "prep_API.json"

[specs]
mp4_output_wc = "ttest_?????.mp4"

[params]
debug = true
groupsize = 48
interpx = 6
extract_count = 0  # 0 = all
overlap = 0 # deprecated
fps = 8

[prep]
cnets = ["HED","POSE","SEG"]
```


There are three stages.

- Preparation
- Animation
- Merging

## Preparation

The *prep* workflow requires:

- The **Save Image Extended** node, and in that node, the **filename_prefix** and **foldername_prefix** must be any name that is all caps, no spaces, followed by `_ZZ`
- The "Load Images" node "directory" field must be `<tmp_dir_name>/ZZ`
- The ControlNet Preprocessor must be set to a resolution that is the same as the final output (this will be automated at some point)

The *prep* stage creates preprocessed ControlNet clips used by **ComfyUI-Video-Helper => Load Images** node, which are then fed into the **Apply ControlNet (Advanced)** node.   

To run the *prep* stage, issue the command:

```
./long_anim_v3.py --stage prep -D <project subdolder>
```
ex:
```
./long_anim_v3.py --stage prep -D /src/settings/ttest
```

Folder names must be absolute.

The *prep* process reads the video assigned in the TOML file, extracts is to a temp folder at an FPS defined in the TOML file.

It then creates subgroups of the extracted frames, each with `groupsize` frames (defined in TOML).  A `groupsize` of 48 is max, as beyond that all movement to destroyed by Animatediff.

Each subgroup is processed, producing `groupsize` collections of images saved as numbered folders in the default ComfyUI input directory.

Note: The ComfyUI folder is './input', and the nodes depend on this.  To allow for multiple project folders, the application outputs to `./INPUTS/<projectName>`, and then symbolically links that propject's folder to `./input`.

Example:
```
./input -> /home/jw/src/ComfyUI/INPUTS/ttest-input/
```
The *prep* stage also copies all image files to the input folder.

Example of input folder preprocessed images for the **HED** ControlNet:

```
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

The *anim* stage requires the file `amin_API.json` in the project setting folder.

Requirements for the `anim-API.json` are are:

- The **Load Images=>directory** field must be the same all-caps name used in the `prep` stage, but instead of being suffixed by `_ZZ`, it should be suffixed by `_00`.

The **Latent Image** node dimensions should match the video dimensions.

The output name for the video must be `OUTPUTVIDEONAME`

The animation stage is initiated with the command:

```
./long_anim_v3.py --stage anim -D <project subdolder>
```
ex:
```
./long_anim_v3.py --stage anim -D /src/settings/ttest
```

The results are video files in the output folder:
```
output/ttest
	ttest_00001.mp4 
	ttest_00001.png 
	ttest_00002.mp4 
	ttest_00002.png
```

### Notes

- As there are only max 48 frames per clip, the prompt can only be 48 elements as well

### Output

Finished clips
```
/home/jw/src/ComfyUI/output/<project.name>/
```

## Merge

The merge stage extracts the above video and creates interpolated images between the last frame of the previous video and the first frame of the following video.  The number of interpolated frames created is determined by  `interpx` in the TOML file.

Note: The interpolation is performed externally by the utilities from https://github.com/vladmandic/rife.git.

*merge* extracts all the videos, then inserts the interpolated frames, then reassembles the video to the final form, which is saved in the project output folder.

The animation stage is initiated with the command:

```
./long_anim_v3.py --stage merge -D <project subdolder>
```
ex:
```
./long_anim_v3.py --stage anim -D /src/settings/ttest
```
To run all as one command in a bash script:

```
CFG="/src/settings/ttest"
./long_anim_v3.py --stage prep -D ${CFG}
./long_anim_v3.py --stage anim -D ${CFG}
./long_anim_v3.py --stage merge -D ${CFG}
```

### Outputs

Extracted video frames (in JPG to save on RAM)
```
/fstmp/00
/fstmp/01 ...
```



### Bugs

- beginning and ending frame appear to be lost
- 
