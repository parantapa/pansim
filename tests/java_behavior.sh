#!/bin/bash

set -Eeuo pipefail

INPUT_DIR="test_data/cva_1"

export START_STATE_FILE="$INPUT_DIR/start_state_ifrac=0.010000,sfrac=0.600000.csv"
export VISIT_FILE_0="$INPUT_DIR/visit_0.csv"
export VISIT_FILE_1="$INPUT_DIR/visit_1.csv"
export VISIT_FILE_2="$INPUT_DIR/visit_2.csv"
export VISIT_FILE_3="$INPUT_DIR/visit_3.csv"
export VISIT_FILE_4="$INPUT_DIR/visit_4.csv"
export VISIT_FILE_5="$INPUT_DIR/visit_5.csv"
export VISIT_FILE_6="$INPUT_DIR/visit_6.csv"

JAR_FILE="../simple_java_behavior/target/pansim_behavior-1.0-SNAPSHOT-jar-with-dependencies.jar"

exec java -jar "$JAR_FILE"
