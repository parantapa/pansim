"""Simple single threaded simulation."""

import os
from collections import defaultdict

import numpy as np
import pandas as pd
from tqdm import tqdm

from .simple_behavior import SimpleBehaviorModel
from .disease_model import DiseaseModel
from . import cli

@cli.command()
def simplesim():
    """Run the simulation."""
    num_ticks = int(os.environ["NUM_TICKS"])
    tick_time = int(os.environ["TICK_TIME"])
    output_file = os.environ["OUTPUT_FILE"]

    print("Loading disease model")
    disease_model = DiseaseModel(os.environ["DISEASE_MODEL_FILE"])

    print("Initializing behavior model")
    behavior_model = SimpleBehaviorModel()

    epicurve = []

    it_1 = range(num_ticks)
    for tick in it_1:
        print("Starting tick %d" % tick)

        state_df = behavior_model.next_state_df
        visit_df = behavior_model.next_visit_df

        print("Computing epicurve")
        state_count = state_df.groupby("current_state").agg({"pid": len}).pid
        epirow = [state_count.get(i, 0) for i in range(disease_model.n_states)]
        epicurve.append(epirow)

        it_2 = visit_df.groupby("lid")
        it_2 = tqdm(it_2, desc="Transmission step", unit="location")
        visit_outputs = defaultdict(list)
        for lid, group in it_2:
            visit_output = disease_model.compute_visit_output(group, behavior_model.attr_names, lid)
            for k, v in visit_output.items():
                visit_outputs[k].append(v)
        visit_outputs.default_factory = None
        visit_outputs = {k: np.hstack(vs) for k, vs in visit_outputs.items()}
        visit_output_df = pd.DataFrame(visit_outputs)

        state_df = state_df.set_index("pid", drop=False)
        columns = ["pid", "group", "current_state", "next_state", "dwell_time", "seed"]

        it_3 = visit_output_df.groupby("pid")
        it_3 = tqdm(it_3, desc="Progression step", unit="person")
        new_states = []
        for pid, group in it_3:
            cur_state = (state_df.at[pid, col] for col in columns)
            new_state = disease_model.compute_progression_output(cur_state, group, tick_time)
            new_states.append(new_state)
        new_state_df = pd.DataFrame(new_states, columns=columns)

        print("Running behavior model")
        behavior_model.run_behavior_model(new_state_df, visit_output_df)

    print("Computing final epicurve.")
    state_count = new_state_df.groupby("current_state").agg({"pid": len}).pid
    epirow = [state_count.get(i, 0) for i in range(disease_model.n_states)]
    epicurve.append(epirow)

    print("Saving epicurve")
    epicurve_df = pd.DataFrame(epicurve, columns=disease_model.model_dict["states"])
    epicurve_df.to_csv(output_file, index=False)

    print("Simulation completed")
