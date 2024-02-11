#!/bin/bash

FILE=$1
INTERP=$2
OUTDIR=$3
cd /home/jw/src/Real-ESRGAN

./inference_realesrgan.py -s ${INTERP} -n RealESRGAN_x4plus -i ${FILE} -o ${OUTDIR} 2>&1 >> /tmp/UPSCALE.log


