#!/bin/bash

# CD to folder that contains all te MP4s to merge

rm /tmp/tmp*.mp4
mkdir safe
cd safe
cp ../*.mp4 ./
genlabels2.py

# for 256x144 clips
perl -pi -e 's/512x25/256x12/gmi' RUN 
perl -pi -e 's/pointsize 25/pointsize 12/gmi' RUN

sh ./RUN 
mergevidX.py --filename "*.mp4" --grid 4x3 -d


# to autoedit toml from the
cd /home/jw/src/sdc/settings/COMFY/
 find |grep spagvik_noise|grep 0_anim.toml|awk '{print "joe "$1}'|grep -v output

# to auto gen bacth from any folder
 find /home/jw/src/sdc/settings/COMFY -type f |grep "mp4"|grep spagvik_noise|grep -v output|awk -F"/" '{print "time unbuffer ./LONGANIM -N "$8"  -A -M | tee run.log"}'|sort -u

# run batch

# coper treh finals to the edxamples folder
find /home/jw/src/sdc/settings/COMFY -type f |grep "final.mp4"|grep -v 23|awk '{print $1}'|sort -u |awk -F "/" '{print "cp "$0" /home/jw/src/sdc/settings/COMFY/examples/noise/"$8".mp4"}'|grep -v good
