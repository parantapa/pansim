#!/bin/bash

set -Eeuo pipefail

SCRIPT="$( realpath "${BASH_SOURCE[0]}" )"

SIMSCRIPT="$( dirname "$SCRIPT" )/distsim_rivanna.sh"

OUPUTDIR="$HOME/var/log"

do_job () {
    env -i HOME="$HOME" PATH="$PATH" "$SIMSCRIPT"
}

submit_job () {
    set -x

    sbatch \
        --job-name distsim \
        --ntasks 1 \
        --cpus-per-task 40 \
        --mem-per-cpu 9G \
        --partition bii \
        --account bii_nssac \
        --time 16:00:00 \
        --output "$OUPUTDIR/distsim-%j.out" \
        "$SCRIPT" do_job
}

if [[ "$#" -eq 0 ]] ; then
    submit_job
elif [[ "$#" -eq 1 ]] && [[ "$1" == "do_job" ]] ; then
    do_job
else
    echo "Invalid arguments"
    exit 1
fi
