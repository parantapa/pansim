"""Simple single threaded simulation."""

import os
import logging
from collections import defaultdict

import click
import numpy as np
import pandas as pd
import pyarrow as pa

from .simple_behavior import SimpleBehaviorModel
from .simple_behavior_java import SimpleJavaBehaviorModel
from .disease_model import DiseaseModel
from .data_schema import make_visit_schema, make_visit_output_schema, make_state_schema

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
    rank_batch = {rank: None for rank in all_ranks}

    if len(df.index):
        df["dest_rank"] = df[scatter_col].map(col_rank)
        for rank, group in df.groupby("dest_rank"):
            batch = serialize_df(group, schema)
            rank_batch[rank] = batch

    for rank, batch in rank_batch.items():
        msg = asys.Message(dest_method, args=[batch])
        asys.send(rank, dest_actor, msg)


class LocationActor:
    """Manager of location specific comuputations."""

    def __init__(self):
        """Initialize."""
        self.behav_ranks = get_config().behav_ranks

        self.visit_batches = []

    def visit(self, visit_batch):
        """Get new visits."""
        LOG.debug("LocationActor: received visit batch")

        self.visit_batches.append(visit_batch)

        if len(self.visit_batches) < len(self.behav_ranks):
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
        if visit_df:
            visit_df = pd.concat(visit_df, axis=0)
        else:
            visit_df = get_config().empty_visit_df

        visit_outputs = defaultdict(list)
        for lid, group in visit_df.groupby("lid"):
            visit_output = disease_model.compute_visit_output(group, attr_names, lid)
            for k, v in visit_output.items():
                visit_outputs[k].append(v)
        visit_outputs.default_factory = None
        visit_outputs = {k: np.hstack(vs) for k, vs in visit_outputs.items()}
        visit_output_df = pd.DataFrame(visit_outputs)

        LOG.debug("LocationActor: Sending visit output to ProgressionActor")
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
        self.behav_ranks = get_config().behav_ranks

        self.current_state_batches = []
        self.visit_output_batches = []

    def current_state(self, current_state_batch):
        """Get the current state."""
        LOG.debug("ProgressionActor: Received current_state")

        self.current_state_batches.append(current_state_batch)
        self.try_compute_prgression_output()

    def visit_output(self, visit_output_batch):
        """Get the visit outputs."""
        LOG.debug("ProgressionActor: Received visit_output")
        self.visit_output_batches.append(visit_output_batch)
        self.try_compute_prgression_output()

    def try_compute_prgression_output(self):
        """Try to run compute_progression_output."""
        if len(self.current_state_batches) < len(self.behav_ranks):
            return
        if len(self.visit_output_batches) < len(asys.ranks()):
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

        current_state_df = [
            unserialize_df(batch)
            for batch in self.current_state_batches
            if batch is not None
        ]
        if current_state_df:
            current_state_df = pd.concat(current_state_df, axis=0)
        else:
            current_state_df = get_config().empty_state_df

        visit_output_df = [
            unserialize_df(batch)
            for batch in self.visit_output_batches
            if batch is not None
        ]
        if visit_output_df:
            visit_output_df = pd.concat(visit_output_df, axis=0)
        else:
            visit_output_df = get_config().empty_visit_output_df

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

        LOG.debug("ProgressionActor: Send out new_state to BehaviorActor")
        df_scatter(
            new_state_df,
            "pid",
            pid_behav_rank,
            behav_ranks,
            state_schema,
            BEHAV_AID,
            "new_state",
        )

        LOG.debug("ProgressionActor: Send out visit_output to BehaviorActor")
        df_scatter(
            visit_output_df,
            "pid",
            pid_behav_rank,
            behav_ranks,
            visit_output_schema,
            BEHAV_AID,
            "visit_output",
        )

        self.current_state_batches = []
        self.visit_output_batches = []


class BehaviorActor:
    """Manager of agent behavior computations."""

    def __init__(self):
        self.visit_output_batches = []
        self.new_state_batches = []

        config = get_config()
        pid_behav_rank = config.pid_behav_rank

        if config.java_behavior == 1:
            LOG.info("BehaviorActor: Using Java behavior model")
            self.behavior_model = SimpleJavaBehaviorModel()
        else:
            myrank = asys.current_rank()
            pids = [pid for pid, rank in pid_behav_rank.items() if rank == myrank]
            seed = config.seed + myrank

            self.behavior_model = SimpleBehaviorModel(seed=seed, pids=pids)

    def visit_output(self, visit_output_batch):
        """Get the visit outputs."""
        LOG.debug("BehaviorActor: Received visit_output")
        self.visit_output_batches.append(visit_output_batch)
        self.try_run_behavior_model()

    def new_state(self, new_state_batch):
        """Get the new state."""
        LOG.debug("BehaviorActor: Received new_state")
        self.new_state_batches.append(new_state_batch)
        self.try_run_behavior_model()

    def try_run_behavior_model(self):
        """Try running the behavior model."""
        if len(self.visit_output_batches) < len(asys.ranks()):
            return
        if len(self.new_state_batches) < len(asys.ranks()):
            return

        LOG.debug("BehaviorActor: Running behavior model")
        self.run_behavior_model()

    def run_behavior_model(self):
        """Run the behavior model for relevant agents."""
        config = get_config()
        disease_model = config.disease_model

        visit_output_df = [
            unserialize_df(batch)
            for batch in self.visit_output_batches
            if batch is not None
        ]
        if visit_output_df:
            visit_output_df = pd.concat(visit_output_df, axis=0)
        else:
            visit_output_df = get_config().empty_visit_output_df

        new_state_df = [
            unserialize_df(batch)
            for batch in self.new_state_batches
            if batch is not None
        ]
        if new_state_df:
            new_state_df = pd.concat(new_state_df, axis=0)
        else:
            new_state_df = get_config().empty_state_df

        self.behavior_model.run_behavior_model(new_state_df, visit_output_df)

        LOG.debug("BehaviorActor: Sening epicurve row to main")
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

        LOG.debug("BehaviorActor: Sending out visit batches to LocationActor")
        df_scatter(
            visit_df,
            "lid",
            lid_rank,
            asys.ranks(),
            visit_schema,
            LOC_AID,
            "visit",
        )

        LOG.debug(
            "BehaviorActor: Sending out current state batches to ProgressionActor"
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
    """Get the rank of a cpu given node and cpu index."""
    n = asys.nodes()[node]
    r = asys.node_ranks(n)[cpu]
    return r


class ConfigActor:
    """Configuration actor."""

    def __init__(self, per_node_behavior, java_behavior):
        """Initialize."""
        nodes = list(asys.nodes())
        current_rank = asys.current_rank()
        current_node = [node for node in nodes if current_rank in asys.node_ranks(node)]
        current_node = current_node[0]
        current_node_index = nodes.index(current_node)
        os.environ["CURRENT_NODE"] = str(current_node_index)

        self.per_node_behavior = per_node_behavior
        self.java_behavior = java_behavior

        self.seed = int(os.environ["SEED"])
        self.tick_time = int(os.environ["TICK_TIME"])
        self.attr_names = os.environ["VISUAL_ATTRIBUTES"].strip().split(",")

        self.disease_model = DiseaseModel(os.environ["DISEASE_MODEL_FILE"])

        self.visit_schema = make_visit_schema(self.attr_names)
        self.visit_output_schema = make_visit_output_schema(self.attr_names)
        self.state_schema = make_state_schema()

        self.empty_visit_df = self.visit_schema.empty_table().to_pandas()
        self.empty_visit_output_df = self.visit_output_schema.empty_table().to_pandas()
        self.empty_state_df = self.state_schema.empty_table().to_pandas()

        lid_part_file = os.environ["LID_PARTITION"]
        pid_part_file = os.environ["PID_PARTITION"]

        lid_part_df = pd.read_csv(lid_part_file)
        pid_part_df = pd.read_csv(pid_part_file)

        self.lid_rank = {}
        for lid, node, cpu in lid_part_df.itertuples(index=False, name=None):
            self.lid_rank[lid] = node_rank(node, cpu)

        self.pid_prog_rank = {}
        self.pid_behav_rank = {}
        for pid, node, cpu in pid_part_df.itertuples(index=False, name=None):
            self.pid_prog_rank[pid] = node_rank(node, cpu)
            if per_node_behavior:
                self.pid_behav_rank[pid] = node_rank(node, 0)
            else:
                self.pid_behav_rank[pid] = node_rank(node, cpu)

        if per_node_behavior:
            self.behav_ranks = [asys.node_ranks(node)[0] for node in asys.nodes()]
        else:
            self.behav_ranks = asys.ranks()


class MainActor:
    """Main Actor."""

    def __init__(self):
        """Initialize."""
        self.num_ticks = int(os.environ["NUM_TICKS"])
        self.output_file = os.environ["OUTPUT_FILE"]
        self.per_node_behavior = bool(int(os.environ.get("PER_NODE_BEHAVIOR", "0")))
        self.java_behavior = int(os.environ.get("JAVA_BEHAVIOR", "0"))
        if self.java_behavior:
            self.per_node_behavior = True

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
                rank,
                CONFIG_AID,
                ConfigActor,
                per_node_behavior=self.per_node_behavior,
                java_behavior=self.java_behavior,
            )
            asys.create_actor(rank, LOC_AID, LocationActor)
            asys.create_actor(rank, PROG_AID, ProgressionActor)

        for rank in self.behav_ranks:
            asys.create_actor(rank, BEHAV_AID, BehaviorActor)

        LOG.info("MainActor: Starting tick %d", self.cur_tick)
        for rank in self.behav_ranks:
            asys.ActorProxy(rank, BEHAV_AID).start_tick()

    def end_tick(self, epicurve_part):
        """Receive the end tick message."""
        LOG.debug("MainActor: Received end_tick")

        self.epicurve_parts.append(epicurve_part)

        # Check if tick ended
        if len(self.epicurve_parts) < len(self.behav_ranks):
            return

        row = [sum(xs) for xs in zip(*self.epicurve_parts)]
        self.tick_epicurve.append(row)
        self.cur_tick += 1
        self.epicurve_parts = []

        # Check if sim should still be running
        if self.cur_tick < self.num_ticks:
            LOG.info("MainActor: Starting tick %d", self.cur_tick)
            for rank in self.behav_ranks:
                asys.ActorProxy(rank, BEHAV_AID).start_tick()
            return

        # Sim has now ended
        LOG.info("Writing epicurve to output file.")
        columns = get_config().disease_model.model_dict["states"]
        epi_df = pd.DataFrame(self.tick_epicurve, columns=columns)
        epi_df.to_csv(self.output_file, index=False)

        asys.stop()


@click.command()
def distsim():
    """Run a distributed simulation."""
    logging.basicConfig(level=logging.INFO)
    asys.start(MAIN_AID, MainActor)
