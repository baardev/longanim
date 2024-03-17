#!/bin/bash

FILE=$1
INTERP=$2
OUTDIR=$3
cd /home/jw/src/Real-ESRGAN

source /home/jw/miniforge3/etc/profile.d/conda.sh
conda activate comfy
#echo "----"
#echo "./inference_realesrgan_video.py -s ${INTERP} -n RealESRGAN_x4plus -i ${FILE} -o  ${OUTDIR} " #2>&1 >> /tmp/UPSCALE.log
#echo "----"
./inference_realesrgan_video.py -s ${INTERP} -n RealESRGAN_x4plus -i ${FILE} -o  ${OUTDIR} #2>&1 >> /tmp/UPSCALE.log
