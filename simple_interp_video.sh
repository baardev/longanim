#!/bin/bash

INPUT_FILE=$1
INTERPX=$2
OUTPUT_FILE_LOC=$3

source /home/jw/miniforge3/etc/profile.d/conda.sh
conda activate Rife

rm -rf /fstmp/sinterv_in
rm -rf /fstmp/sinterv_out
mkdir /fstmp/sinterv_in
mkdir /fstmp/sinterv_out

ffmpeg -y -loglevel warning -i ${INPUT_FILE} -r 8/1 /fstmp/sinterv_in/%09d.png


SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

PYTHON_SCRIPTS_DIR="$PYTHON_DIR/Scripts;/home/jw/store/src/ComfyUI/custom_nodes/comfyui-reactor-node/"
export PATH="$PYTHON_SCRIPTS_DIR:$PYTHON_LIB_DIR:$PYTHON_DIR:$PATH"

cd ~/src/rife

./interpolate.py \
--input /fstmp/sinterv_in \
--output /fstmp/sinterv_out \
--buffer 0 \
--multi ${INTERPX} \
--change 0.01 \
--model rife/flownet-v46.pkl


#ffmpeg -y -loglevel warning -framerate $(($INTERPX * 8)) -pattern_type glob -i '/fstmp/sinterv_out/*.png'  -c:v libx264 -pix_fmt yuv420p ${OUTPUT_FILE_LOC}/out_ix$(($INTERPX * 8)).mp4
ffmpeg -y -loglevel warning -framerate $(($INTERPX * 8)) -pattern_type glob   -i '/fstmp/sinterv_out/*.png' -c:v libx264 -pix_fmt yuv420p -profile:v main -coder 0 -crf 22 -threads 0 ${OUTPUT_FILE_LOC}/final_rife_$(($INTERPX * 8)).mp4
