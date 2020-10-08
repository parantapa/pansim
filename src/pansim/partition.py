"""Create the location visit paritioning."""

import math
import heapq
from collections import defaultdict, Counter

import click
import pandas as pd

from . import cli


def do_partition(visit_df, n_nodes, n_cpu_per_node):
    """Parition locations and persons."""
    n_nodes = int(n_nodes)
    n_cpu_per_node = int(n_cpu_per_node)

    print("Creating lid <--> pid mappings")
    lid_pids = defaultdict(set)
    pid_lids = defaultdict(set)
    for lid, pid in zip(visit_df.lid, visit_df.pid):
        lid_pids[lid].add(pid)
        pid_lids[pid].add(lid)
    lid_pids.default_factory = None
    pid_lids.default_factory = None

    lids = sorted(lid_pids)
    pids = sorted(pid_lids)

    print("Computing location load")
    lid_w = dict()
    for lid in lids:
        w = len(lid_pids[lid])
        w = w * math.log2(w + 1.0)
        lid_w[lid] = w

    n_parts = n_nodes * n_cpu_per_node

    print("Assigning locations to partitions")
    part_heap = [(0.0, part) for part in range(n_parts)]
    lid_part = dict()
    for lid, w in sorted(lid_w.items(), key=lambda x: -x[1]):
        load, part = heapq.heappop(part_heap)
        lid_part[lid] = part
        load = load + w
        heapq.heappush(part_heap, (load, part))

    print("Creating location parition dataframe")
    data = []
    for lid in lids:
        part = lid_part[lid]
        node = part // n_cpu_per_node
        cpu = part % n_cpu_per_node
        row = (lid, node, cpu)
        data.append(row)
    columns = ["lid", "node", "cpu"]
    lid_part_df = pd.DataFrame(data, columns=columns)

    print("Assigning persons to partitions")
    pid_part = dict()
    for pid, lids in pid_lids.items():
        part_ctr = Counter(lid_part[lid] for lid in lids)
        part = part_ctr.most_common(1)[0][0]
        pid_part[pid] = part

    print("Creating person parition dataframe")
    data = []
    for pid in pids:
        part = pid_part[pid]
        node = part // n_cpu_per_node
        cpu = part % n_cpu_per_node
        row = (pid, node, cpu)
        data.append(row)
    columns = ["pid", "node", "cpu"]
    pid_part_df = pd.DataFrame(data, columns=columns)

    return lid_part_df, pid_part_df


@cli.command()
@click.option(
    "-l",
    "--location-partition",
    type=click.Path(),
    help="The location parititon output file.",
)
@click.option(
    "-p",
    "--person-partition",
    type=click.Path(),
    help="The person parition output file.",
)
@click.option("-n", "--num-nodes", default=1, help="Number of nodes")
@click.option("-c", "--num-cpu-per-node", default=2, help="Number of cpus per node")
@click.argument("visit-file", nargs=-1)
def partition(
    location_partition, person_partition, num_nodes, num_cpu_per_node, visit_file
):
    """Parition the locations and persons onto cpus."""
    visit_df = []
    for fname in visit_file:
        print("Reading ", fname)
        df = pd.read_csv(fname)
        visit_df.append(df)
    visit_df = pd.concat(visit_df, axis=0)

    lid_part_df, pid_part_df = do_partition(visit_df, num_nodes, num_cpu_per_node)

    print("Writing ", location_partition)
    lid_part_df.to_csv(location_partition, index=False)

    print("Writing ", person_partition)
    pid_part_df.to_csv(person_partition, index=False)
