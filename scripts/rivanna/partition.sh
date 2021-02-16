#!/bin/bash
# Partition the pids and lids

set -Eeuo pipefail
set -x

for county in charlottesville richmond albemarle fluvanna goochland hanover henrico louisa; do
    nodes=1
    for cpus in 5 10 20 40 ; do
        pansim partition \
            -l lid__county=${county}__n=${nodes}__c=${cpus}.csv \
            -p pid__county=${county}__n=${nodes}__c=${cpus}.csv \
            -n ${nodes} \
            -c ${cpus} \
            visits_${county}_*.csv
    done

    cpus=40
    for nodes in 1 2 4 ; do
        pansim partition \
            -l lid__county=${county}__n=${nodes}__c=${cpus}.csv \
            -p pid__county=${county}__n=${nodes}__c=${cpus}.csv \
            -n ${nodes} \
            -c ${cpus} \
            visits_${county}_*.csv
    done
done
