"""Simple behavior model."""

import os
import random

import pandas as pd

from .disease_model import SEED_MIN, SEED_MAX, NULL_STATE, NULL_DWELL_TIME

def read_start_state_df(fname, seed):
    """Return the start state dataframe."""
    random.seed(seed)

    start_state_df = pd.read_csv(fname)
    start_state_df = start_state_df.rename({
        "start_state": "current_state"
    }, axis=1)
    start_state_df["next_state"] = NULL_STATE
    start_state_df["dwell_time"] = NULL_DWELL_TIME
    start_state_df["seed"] = [random.randint(SEED_MIN, SEED_MAX) for _ in start_state_df.index]

    return start_state_df

def read_visit_df(fname, state_df, attr_names):
    """Return the visit dataframe."""
    visit_df = pd.read_csv(fname)
    visit_df["group"] = 0
    visit_df["state"] = 0
    visit_df["behavior"] = 0
    for name in attr_names:
        visit_df[name] = 0

    pid_i = {pid: i for i, pid in zip(state_df.index, state_df.pid)}

    for index, pid in zip(visit_df.index, visit_df.pid):
        state_index = pid_i[pid]
        visit_df.state[index] = state_df.current_state[state_index]
        visit_df.group[index] = state_df.group[state_index]

    return visit_df

class SimpleBehaviorModel:
    """Simple behavior model."""

    def __init__(self):
        """Initialize."""
        self.seed = int(os.environ["SEED"])
        self.num_ticks = int(os.environ["NUM_TICKS"])
        self.max_visits = int(os.environ["MAX_VISITS"])

        self.attr_names = os.environ["VISUAL_ATTRIBUTES"].strip().split(",")

        self.start_state_file = os.environ["START_STATE_FILE"]
        self.visit_files = []
        for i in range(self.num_ticks):
            key = "VISIT_FILE_%d" % i
            self.visit_files.append(os.environ[key])


        self.start_state_df = read_start_state_df(self.start_state_file, self.seed)

        self.next_tick = 0
        if self.next_tick < self.num_ticks:
            self.next_state_df = self.start_state_df
            self.next_visit_df = read_visit_df(self.visit_files[self.next_tick], self.start_state_df, self.attr_names)
        else:
            self.next_state_df = None
            self.next_visit_df = None

    def run_behavior_model(self, cur_state_df, visit_output_df):
        """Run the behavior model."""
        _ = visit_output_df

        self.next_tick += 1

        if self.next_tick < self.num_ticks:
            self.next_state_df = cur_state_df
            self.next_visit_df = read_visit_df(self.visit_files[self.next_tick], cur_state_df, self.attr_names)
        else:
            self.next_state_df = None
            self.next_visit_df = None
