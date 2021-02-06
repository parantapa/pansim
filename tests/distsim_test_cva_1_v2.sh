#!/bin/bash
# Simple sim test cva_1

set -Eeuo pipefail

export SEED=42
export NUM_TICKS=7
export TICK_TIME=1
export MAX_VISITS=204000
export VISUAL_ATTRIBUTES=coughing,mask,sdist

export DISEASE_MODEL_FILE="disease_models/seiar.toml"

INPUT_DIR="simple_sim_data/cva_1"

export START_STATE_FILE="$INPUT_DIR/start_state_ifrac=0.010000,sfrac=0.600000.csv"
export VISIT_FILE_0="$INPUT_DIR/visit_0.csv"
export VISIT_FILE_1="$INPUT_DIR/visit_1.csv"
export VISIT_FILE_2="$INPUT_DIR/visit_2.csv"
export VISIT_FILE_3="$INPUT_DIR/visit_3.csv"
export VISIT_FILE_4="$INPUT_DIR/visit_4.csv"
export VISIT_FILE_5="$INPUT_DIR/visit_5.csv"
export VISIT_FILE_6="$INPUT_DIR/visit_6.csv"

export LID_PARTITION="$INPUT_DIR/lid_partition.csv"
export PID_PARTITION="$INPUT_DIR/pid_partition.csv"

export OUTPUT_FILE="epicurve.csv"

export PER_NODE_BEHAVIOR=1
export JAVA_BEHAVIOR=2

export START_EXPOSED_SEED=300
export TICK_EXPOSED_SEED=50

N_CPUS=6
export XACTOR_MAX_SEND_BUFFERS=$((4 * $N_CPUS))
#export XACTOR_PROFILE_DIR=.

TIMEFORMAT="Simulation runtime: %E"
time mpiexec -n $N_CPUS pansim distsim
