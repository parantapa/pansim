"""Simple behavior model."""

import os
import random
from itertools import count

import pyarrow.csv as csv

from .disease_model import SEED_MIN, SEED_MAX, NULL_STATE, NULL_DWELL_TIME

def read_start_state_df(fname, seed):
    """Return the start state dataframe."""
    random.seed(seed)

    start_state_df = csv.read_csv(fname).to_pandas()
    start_state_df = start_state_df.rename({
        "start_state": "current_state"
    }, axis=1)
    start_state_df["next_state"] = NULL_STATE
    start_state_df["dwell_time"] = NULL_DWELL_TIME
    start_state_df["seed"] = [random.randint(SEED_MIN, SEED_MAX) for _ in start_state_df.index]

    return start_state_df

def setup_visit_df(visit_df, state_df, attr_names):
    """Return the visit dataframe."""
    visit_df = visit_df.copy()
    visit_df["group"] = 0
    visit_df["state"] = 0
    visit_df["behavior"] = 0
    for name in attr_names:
        visit_df[name] = 0

    pid_i = {pid: i for i, pid in zip(state_df.index, state_df.pid)}

    for index, pid in zip(visit_df.index, visit_df.pid):
        state_index = pid_i[pid]
        visit_df.at[index, "state"] = state_df.at[state_index, "current_state"]
        visit_df.at[index, "group"] = state_df.at[state_index, "group"]

    return visit_df

class SimpleBehaviorModel:
    """Simple behavior model."""

    def __init__(self):
        """Initialize."""
        self.seed = int(os.environ["SEED"])
        self.attr_names = os.environ["VISUAL_ATTRIBUTES"].strip().split(",")

        self.start_state_file = os.environ["START_STATE_FILE"]
        self.visit_files = []
        for i in count(0):
            key = "VISIT_FILE_%d" % i
            if key not in os.environ:
                break

            fname = os.environ[key]
            self.visit_files.append(fname)

        self.start_state_df = read_start_state_df(self.start_state_file, self.seed)
        self.visit_dfs_raw = []
        for fname in self.visit_files:
            df = csv.read_csv(fname).to_pandas()
            self.visit_dfs_raw.append(df)

        self.next_tick = 0

        self.next_state_df = self.start_state_df
        idx = self.next_tick % len(self.visit_dfs_raw)
        self.next_visit_df = setup_visit_df(self.visit_dfs_raw[idx], self.start_state_df, self.attr_names)

    def run_behavior_model(self, cur_state_df, visit_output_df):
        """Run the behavior model."""
        _ = visit_output_df

        self.next_tick += 1

        self.next_state_df = cur_state_df
        idx = self.next_tick % len(self.visit_dfs_raw)
        self.next_visit_df = setup_visit_df(self.visit_dfs_raw[idx], cur_state_df, self.attr_names)
