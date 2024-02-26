Run 'masking' to create a video of a mask

# `1_prep.json`

- Extract the source video by *n* frames into a folder.  The default is **fstmp/ZZ**.  Extract with 

  ```
  ffmpeg -y -loglevel warning -i source_video.mp4 -r 24/1 /fstmp/ZZ/%09d.png
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

  
