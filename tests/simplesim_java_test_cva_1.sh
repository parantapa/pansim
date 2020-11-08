#!/bin/bash
# Simple sim test cva_1

set -Eeuo pipefail

export NUM_TICKS=1
export TICK_TIME=1
export MAX_VISITS=204000
export VISUAL_ATTRIBUTES=coughing,mask,sdist

export DISEASE_MODEL_FILE="disease_models/seiar.toml"

export OUTPUT_FILE="epicurve.csv"
export JAVA_BEHAVIOR=1

TIMEFORMAT="Simulation runtime: %E"
time pansim simplesim
