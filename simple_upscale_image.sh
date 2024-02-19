#!/bin/bash

FILE=$1
SCALE=$2
OUTDIR=$3
cd /home/jw/src/Real-ESRGAN

source /home/jw/miniforge3/etc/profile.d/conda.sh
conda activate Rife



./inference_realesrgan.py -s ${SCALE} -n RealESRGAN_x${SCALE}plus -i ${FILE} -o ${OUTDIR} #2>&1 >> /tmp/UPSCALE.log


