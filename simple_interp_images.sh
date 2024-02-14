#!/bin/bash

INPUT_FILE_LOC=$1
INTERPX=$2
OUTPUT_FILE_LOC=$3

source /home/jw/miniforge3/etc/profile.d/conda.sh
conda activate Rife

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

PYTHON_SCRIPTS_DIR="$PYTHON_DIR/Scripts;/home/jw/store/src/ComfyUI/custom_nodes/comfyui-reactor-node/"
export PATH="$PYTHON_SCRIPTS_DIR:$PYTHON_LIB_DIR:$PYTHON_DIR:$PATH"

cd ~/src/rife

./interpolate.py \
--input ${INPUT_FILE_LOC} \
--output ${OUTPUT_FILE_LOC} \
--buffer 0 \
--multi ${INTERPX} \
--change 0.01 \
--model rife/flownet-v46.pkl


