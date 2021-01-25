#!/bin/bash
# Simple sim test cva_1

set -Eeuo pipefail

set +u
eval "$(conda shell.bash hook)"
conda activate pansim
set -u

set -x

export SEED=42
export NUM_TICKS=7
export TICK_TIME=1
export MAX_VISITS=204000
export VISUAL_ATTRIBUTES=coughing,mask,sdist

INPUT_DIR="/scratch/pb5gj/2020-pansim-test-inputs/2021-01-25"
COUNTY="charlottesville"
export OUTPUT_FILE="epicurve.csv"

export DISEASE_MODEL_FILE="$INPUT_DIR/seiar_1.toml"

export START_STATE_FILE="$INPUT_DIR/start_state_${COUNTY}_ifrac=0.01_sfrac=0.6.csv"

export VISIT_FILE_0="$INPUT_DIR/visits_${COUNTY}_0.csv"
export VISIT_FILE_1="$INPUT_DIR/visits_${COUNTY}_1.csv"
export VISIT_FILE_2="$INPUT_DIR/visits_${COUNTY}_2.csv"
export VISIT_FILE_3="$INPUT_DIR/visits_${COUNTY}_3.csv"
export VISIT_FILE_4="$INPUT_DIR/visits_${COUNTY}_4.csv"
export VISIT_FILE_5="$INPUT_DIR/visits_${COUNTY}_5.csv"
export VISIT_FILE_6="$INPUT_DIR/visits_${COUNTY}_6.csv"

export PER_NODE_BEHAVIOR=0
export JAVA_BEHAVIOR=0

PANSIM_CPUS=20

export XACTOR_MAX_SEND_BUFFERS=$((4 * $PANSIM_CPUS))
export LID_PARTITION="$INPUT_DIR/lid_${COUNTY}_${PANSIM_CPUS}.csv"
export PID_PARTITION="$INPUT_DIR/pid_${COUNTY}_${PANSIM_CPUS}.csv"

TIMEFORMAT="Simulation runtime: %E"
time mpiexec -n $PANSIM_CPUS pansim distsim
