"""Simple single threaded simulation."""

import os
import logging
from collections import defaultdict

import numpy as np
import pandas as pd
import pyarrow as pa

from .simple_behavior import SimpleBehaviorModel
from .disease_model import DiseaseModel
from .data_schema import make_visit_schema, make_visit_output_schema, make_state_schema
from . import cli

import xactor as asys

MAIN_AID = "main_actor"
LOC_AID = "location_actor"
PROG_AID = "progression_actor"
BEHAV_AID = "behavior_actor"
CONFIG_AID = "config_actor"

LOG = asys.getLogger(__name__)


def get_config():
    """Return the local configuration mangager."""
    return asys.local_actor(CONFIG_AID)


def serialize_df(df, schema):
    """Serialize a pandas dataframe to bytes."""
    sink = pa.BufferOutputStream()
    writer = pa.ipc.new_file(sink, schema)
    batch = pa.record_batch(df, schema=schema)
    writer.write_batch(batch)
    writer.close()
    raw = sink.getvalue().to_pybytes()
    return raw


def unserialize_df(raw):
    """Reconstruct a pandas dataframe from bytes."""
    fobj = pa.ipc.open_file(raw)
    batch = fobj.get_batch(0)
    df = batch.to_pandas()
    return df


def df_scatter(df, scatter_col, col_rank, all_ranks, schema, dest_actor, dest_method):
    """Scatter the dataframe to all ranks."""
    df["dest_rank"] = df[scatter_col].map(col_rank)

    sent_ranks = set()
    for rank, group in df.groupby("dest_rank"):
        batch = serialize_df(group, schema)

        msg = asys.Message(dest_method, args=[batch])
        asys.send(rank, dest_actor, msg)
        sent_ranks.add(rank)

    for rank in all_ranks:
        if rank not in sent_ranks:
            msg = asys.Message(dest_method, args=[None])
            asys.send(rank, dest_actor, msg)


class LocationActor:
    """Manager of location specific comuputations."""

    def __init__(self):
        """Initialize."""
        self.visit_batches = []

    def visit(self, visit_batch):
        """Get new visits."""
        self.visit_batches.append(visit_batch)
        if len(self.visit_batches) < len(asys.ranks()):
            return

        self.compute_visit_output()

    def compute_visit_output(self):
        """Compute the visit outputs."""
        config = get_config()
        disease_model = config.disease_model
        attr_names = config.attr_names
        pid_prog_rank = config.pid_prog_rank
        visit_output_schema = config.visit_output_schema

        visit_df = [
            unserialize_df(batch) for batch in self.visit_batches if batch is not None
        ]
        visit_df = pd.concat(visit_df, axis=0)

        visit_outputs = defaultdict(list)
        for lid, group in visit_df.groupby("lid"):
            visit_output = disease_model.compute_visit_output(group, attr_names, lid)
            for k, v in visit_output.items():
                visit_outputs[k].append(v)
        visit_outputs.default_factory = None
        visit_outputs = {k: np.hstack(vs) for k, vs in visit_outputs.items()}
        visit_output_df = pd.DataFrame(visit_outputs)

        df_scatter(
            visit_output_df,
            "pid",
            pid_prog_rank,
            asys.ranks(),
            visit_output_schema,
            PROG_AID,
            "visit_output",
        )

        self.visit_batches = []


class ProgressionActor:
    """Manager for disease progression computations."""

    def __init__(self):
        """Initialize."""
        self.current_state_batch = None
        self.visit_output_batches = []

    def current_state(self, current_state_batch):
        """Get the current state."""
        self.current_state_batch = current_state_batch

        if (
            len(self.visit_output_batches) < len(asys.ranks())
            or self.current_state_batch is None
        ):
            return

        self.compute_progression_output()

    def visit_output(self, visit_output_batch):
        """Get the visit outputs."""
        self.visit_output_batches.append(visit_output_batch)

        if (
            len(self.visit_output_batches) < len(asys.ranks())
            or self.current_state_batch is None
        ):
            return

        self.compute_progression_output()

    def compute_progression_output(self):
        """Compute disease progression."""
        config = get_config()
        disease_model = config.disease_model
        pid_behav_rank = config.pid_behav_rank
        behav_ranks = config.behav_ranks
        visit_output_schema = config.visit_output_schema
        state_schema = config.state_schema
        tick_time = config.tick_time

        current_state_df = unserialize_df(self.current_state_batch)
        visit_output_df = [
            unserialize_df(batch)
            for batch in self.visit_output_batches
            if batch is not None
        ]
        visit_output_df = pd.concat(visit_output_df, axis=0)

        current_state_df = current_state_df.set_index("pid", drop=False)
        columns = ["pid", "group", "current_state", "next_state", "dwell_time", "seed"]

        new_states = []
        for pid, group in visit_output_df.groupby("pid"):
            cur_state = (current_state_df.at[pid, col] for col in columns)
            new_state = disease_model.compute_progression_output(
                cur_state, group, tick_time
            )
            new_states.append(new_state)
        new_state_df = pd.DataFrame(new_states, columns=columns)

        df_scatter(
            new_state_df,
            "pid",
            pid_behav_rank,
            behav_ranks,
            state_schema,
            BEHAV_AID,
            "new_state",
        )

        df_scatter(
            visit_output_df,
            "pid",
            pid_behav_rank,
            behav_ranks,
            visit_output_schema,
            BEHAV_AID,
            "visit_output",
        )

        self.current_state_batch = None
        self.visit_output_batches = []


class BehaviorActor:
    """Manager of agent behavior computations."""

    def __init__(self):
        self.visit_output_batches = []
        self.new_state_batches = []

        config = get_config()
        pid_behav_rank = config.pid_behav_rank
        myrank = asys.current_rank()
        pids = [pid for pid, rank in pid_behav_rank.items() if rank == myrank]
        seed = config.seed + myrank

        self.behavior_model = SimpleBehaviorModel(seed=seed, pids=pids)

    def visit_output(self, visit_output_batch):
        """Get the visit outputs."""
        self.visit_output_batches.append(visit_output_batch)

        if len(self.visit_output_batches) < len(asys.ranks()):
            return
        if len(self.new_state_batches) < len(asys.ranks()):
            return

        self.run_behavior_model()

    def new_state(self, new_state_batch):
        """Get the new state."""
        self.new_state_batches.append(new_state_batch)

        if len(self.visit_output_batches) < len(asys.ranks()):
            return
        if len(self.new_state_batches) < len(asys.ranks()):
            return

    def run_behavior_model(self):
        """Run the behavior model for relevant agents."""
        config = get_config()
        disease_model = config.disease_model

        visit_output_df = [
            unserialize_df(batch)
            for batch in self.visit_output_batches
            if batch is not None
        ]
        visit_output_df = pd.concat(visit_output_df, axis=0)

        new_state_df = [
            unserialize_df(batch)
            for batch in self.new_state_batches
            if batch is not None
        ]
        new_state_df = pd.concat(new_state_df, axis=0)

        self.behavior_model.run_behavior_model(new_state_df, visit_output_df)

        state_count = new_state_df.groupby("current_state").agg({"pid": len}).pid
        epirow = [state_count.get(i, 0) for i in range(disease_model.n_states)]

        asys.ActorProxy(asys.MASTER_RANK, MAIN_AID).end_tick(epirow)

        self.visit_output_batches = []
        self.new_state_batches = []

    def start_tick(self):
        """Start the next tick."""
        config = get_config()
        lid_rank = config.lid_rank
        pid_prog_rank = config.pid_prog_rank
        visit_schema = config.visit_schema
        state_schema = config.state_schema

        current_state_df = self.behavior_model.next_state_df
        visit_df = self.behavior_model.next_visit_df

        df_scatter(
            visit_df,
            "lid",
            lid_rank,
            asys.ranks(),
            visit_schema,
            LOC_AID,
            "visit",
        )

        df_scatter(
            current_state_df,
            "pid",
            pid_prog_rank,
            asys.ranks(),
            state_schema,
            PROG_AID,
            "current_state",
        )

def node_rank(node, cpu):
    n = asys.nodes()[node]
    r = asys.node_ranks(n)[cpu]
    return r


class ConfigActor:
    """Configuration actor."""

    def __init__(self, per_node_behavior=False):
        """Initialize."""
        self.seed = int(os.environ["SEED"])
        self.tick_time = int(os.environ["TICK_TIME"])
        self.disease_model = DiseaseModel(os.environ["DISEASE_MODEL_FILE"])
        self.attr_names = os.environ["VISUAL_ATTRIBUTES"].strip().split(",")
        self.visit_schema = make_visit_schema(self.attr_names)
        self.visit_output_schema = make_visit_output_schema(self.attr_names)
        self.state_schema = make_state_schema()

        lid_part_file = os.environ["LID_PARTITION"]
        pid_part_file = os.environ["PID_PARTITION"]

        lid_part_df = pd.read_csv(lid_part_file)
        pid_part_df = pd.read_csv(pid_part_file)

        self.lid_rank = {
            lid: node_rank(node, cpu)
            for lid, node, cpu in lid_part_df.itertuples(index=False, name=None)
        }
        self.pid_prog_rank = {
            pid: node_rank(node, cpu)
            for pid, node, cpu in pid_part_df.itertuples(index=False, name=None)
        }

        if per_node_behavior:
            self.pid_behav_rank = {
                pid: node_rank(node, cpu)
                for pid, node, cpu in pid_part_df.itertuples(index=False, name=None)
            }
            self.behav_ranks = [asys.node_ranks(node)[0] for node in asys.nodes()]
        else:
            self.pid_behav_rank = {
                pid: node_rank(node, cpu)
                for pid, node, cpu in pid_part_df.itertuples(index=False, name=None)
            }
            self.behav_ranks = asys.ranks()


class MainActor:
    """Main Actor."""

    def __init__(self):
        """Initialize."""
        self.num_ticks = int(os.environ["NUM_TICKS"])
        self.output_file = os.environ["OUTPUT_FILE"]
        self.per_node_behavior = False

        self.epicurve_parts = []
        self.cur_tick = 0

        self.tick_epicurve = []

        if self.per_node_behavior:
            self.behav_ranks = [asys.node_ranks(node)[0] for node in asys.nodes()]
        else:
            self.behav_ranks = asys.ranks()

    def main(self):
        """Run the simulation."""
        for rank in asys.ranks():
            asys.create_actor(
                rank, CONFIG_AID, ConfigActor, per_node_behavior=self.per_node_behavior
            )
            asys.create_actor(rank, LOC_AID, LocationActor)
            asys.create_actor(rank, PROG_AID, ProgressionActor)

        for rank in self.behav_ranks:
            asys.create_actor(rank, BEHAV_AID, BehaviorActor)

        LOG.info("Starting tick %d", self.cur_tick)
        for rank in self.behav_ranks:
            asys.ActorProxy(rank, BEHAV_AID).start_tick()

    def end_tick(self, epicurve_part):
        """Receive the end tick message."""
        self.epicurve_parts.append(epicurve_part)

        if len(self.epicurve_parts) < len(self.behav_ranks):
            return

        row = [sum(xs) for xs in zip(*self.epicurve_parts)]
        self.tick_epicurve.append(row)
        self.cur_tick += 1
        self.epicurve_parts = []

        LOG.info("Starting tick %d", self.cur_tick)

        for rank in self.behav_ranks:
            asys.ActorProxy(rank, BEHAV_AID).start_tick()

        if self.cur_tick < self.num_ticks:
            return

        columns = ["pid", "group", "current_state", "next_state", "dwell_time", "seed"]
        epi_df = pd.DataFrame(self.tick_epicurve, columns=columns)
        epi_df.to_csv(self.output_file, index=False)

        asys.stop()

@cli.command()
def distsim():
    """Run the simulation."""
    logging.basicConfig(level=logging.INFO)
    asys.start(MAIN_AID, MainActor)

