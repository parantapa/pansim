#!/bin/bash
# Simple sim test cva_1

set -Eeuo pipefail

export SEED=42
export NUM_TICKS=7
export TICK_TIME=1
export MAX_VISITS=204000
export VISUAL_ATTRIBUTES=coughing,mask,sdist

export DISEASE_MODEL_FILE="disease_models/seiar.toml"

export LID_PARTITION="$INPUT_DIR/lid_partition.csv"
export PID_PARTITION="$INPUT_DIR/pid_partition.csv"

export OUTPUT_FILE="epicurve.csv"

export PER_NODE_BEHAVIOR=1
export JAVA_BEHAVIOR=1


N_CPUS=6
export XACTOR_MAX_SEND_BUFFERS=$((4 * $N_CPUS))
#export XACTOR_PROFILE_DIR=.

TIMEFORMAT="Simulation runtime: %E"
time mpiexec --mca mpi_yield_when_idle 1 -n $N_CPUS \
    pansim distsim
