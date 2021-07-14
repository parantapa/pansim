#!/bin/bash
# Simple sim test cva_1

set -Eeuo pipefail

export SEED=42
export NUM_TICKS=1
export TICK_TIME=1
export MAX_VISITS=204000
export VISUAL_ATTRIBUTES=coughing,mask,sdist

export DISEASE_MODEL_FILE="disease_models/seiar.toml"

export OUTPUT_FILE="simplesim_java_test_cva_epicurve.csv"

export JAVA_BEHAVIOR=1
export JAVA_BEHAVIOR_SCRIPT="./java_behavior.sh"

TIMEFORMAT="Simulation runtime: %E"
time pansim simplesim
