#!/bin/bash 

#! the folder you layer-saved to
cd /fstmp/merged1

rm *merged*

BG=`find -name "*Background*"`

#! 'FACE' must be in the layer name
for I in *FACE*.png; do
#! use prebuilt background image
    convert -page +0+0 ${BG} \
    -page +0+0 $I \
    -background none -layers merge +repage $I-merged.png
done

#! now save a video
ffmpeg -y -loglevel warning -framerate 8 -pattern_type glob -i '*merged*.png'  -c:v libx264 -pix_fmt yuv420p merged.mp4

ffmpeg  -y -loglevel warning -i merged.mp4 -vf reverse -af areverse reversed.mp4

