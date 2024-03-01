#  A continuation of `longanim/README.md`



# `1_prep.json`

- Extract the source video by *n* frames into a tmp folder.  Extract with 

  ```
  ffmpeg -y -loglevel warning -i source_video.mp4 -r 12/1 /fstmp/liza_12fps/%09d.png
  ```

- Unmute (or add) the CNs that will be used.

- Update **Res**, **Rate**.  In **Load Images** node, **image_load_cap** should be no more that 48.

- Submit queue

- NOTE: If using **LONGANIM** w/**AnimateDiff**, **video_test.json** will only load 48 frames max, no matter how many there are.  For multiple sets of 48, see 'LONGANIM'

# `video_test.json`

- Drop any 512x512 images into **<input_dir>/01.png** and **02.png**
  - the new input image will be a 50/50 (default) morph of the 2 images.  Up to 6 images can be morphed
  
- Drop any 512x512 video into **<input_dir>/video.mp4**

- Created the CN files needed with **1_prep.json** 

- Move the newly created folder in **<output_dir>** to **<input_dir>** (if they are different)

- in **video_test.json** update groups **CN_01**, **CN_02**, etc., to point to the appropriate folders that were just created.

- Update prompts, or other variables, and submit queue

  

# `LONGANIM`

To use these with LONGAMIN.

```bash
cd ~/src/longanim
```
Extract files of` PROJECTS/boat/512x512_annlong.mp4` at 8 fps to `/xfstmp/ann_8fps` (you need to make that directory manually)

Edit `PROJECTS/boat/1_prop.json` in the ComfyUI GUI  (or manually) and make sure the base name of the input videofiles, such as 'ann' (as in `512x512_ann_8fps.mp4` or 'liza' is correct.  Save a `1_prep_API.json`

edit `PROJECTS/boat/0_anim.toml` and adjust settings

Run 
```bash
./LONGANIM -P
```
### WARNING: '-P' This WIPES OUT EVERYTHING in `/fstmp` AND `PROJECTS/boat/outfile_512`
This will create folder in `PROJECTS/boat/output_512` named 
```bash
ann_8fps_POZE_00
ann_8fps_POZE_01
...
```
These folder contain the preprocessed CN images that are used as inoput for `1_anim.json`

Symlink or rename these folders to just `POSE_??`, as that is what `1_anim.json` is looking for.

edit `PROJECTS/boat/1_anim.json` and adjust settings

There MUST be two fiels in the inoput directory (which in this case is also the output directory", named `IMAGE01.png`, and `IMAGE02.png`.  They are jus there to allow stubs in the fields which will get replaced.

Run

```
./LONGANIM -A
```








############################################################33

```
cd ~/src/longanim/merge
mkdir images_boat
```

The `outdir` is created automatically in `src/longanim/PROJECTS/boat/output_512` and acts as `indir` and `outdir` in thios process.  The `512` spec comes from the TOML file.

~~Copy the folder that contains the CN files for whatever~~ 
~~cp ~/src/longanim/PROJECTS/boat/input_512/ann_8fps_POZE_ZZ outdir/POSE_ZZ~~


ln -fs images_boat IMAGES

cd IMAGES

```
cp ../images_test/mergerun.toml ./ (edit)
```
Edit/check ***w***, ***h***, ***project*** to match the new params
Comment ou ***masks_0/***1 (most likely
```
cp ../images_test/interp_v0.json ./
cp ../images_test/qmasks_v0.json ./
cp ../images_test/LOCAL_START ./
cp ../../examples/1_prep.json ./
```

Opel 1_prep.json. Mute/unmute whatever CNs apply
Update 'Load Images" to point top teh cirrect folder.  In this case that is `/fstmp/ann_8fps` becauser they were aldeady extracted to that location.  This is th eonly adjustmet that needs to be mnade.  All otehr adjustmets are mde by the programs.



[fSTART]()













