#!/bin/bash

set -Eeuo pipefail

SCRIPT="$( realpath "${BASH_SOURCE[0]}" )"

SIMSCRIPT="$( dirname "$SCRIPT" )/distsim_rivanna.sh"
OUPUTDIR="$HOME/var/log"

do_job () {
    simscript="$1"
    county="$2"

    export COUNTY="$county"
    "$simscript"
}

submit_job () {
    set -x

    for county in charlottesville richmond ; do
        nodes=1
        for cpus in 5 10 20 40 ; do
            for replicate in $(seq 5) ; do
                key="count=${county}__n=${nodes}__c=${cpus}__replicate=${replicate}"

                sbatch \
                    --job-name distsim \
                    --nodes $nodes \
                    --ntasks-per-node $cpus \
                    --cpus-per-task 1 \
                    --mem-per-cpu 9G \
                    --partition bii \
                    --account distributed-2apl  \
                    --time 2:00:00 \
                    --output "$OUPUTDIR/distsim__${key}.%j.out" \
                    "$SCRIPT" "$SIMSCRIPT" "$county"
            done
        done
    done
}

if [[ "$#" -eq 0 ]] ; then
    submit_job
else
    do_job "$@"
fi
