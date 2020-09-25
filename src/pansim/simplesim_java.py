"""Simple single threaded simulation."""

import os

import pandas as pd
from tqdm import tqdm

from .simple_java_behavior import SimpleJavaBehaviorModel
from .disease_model import DiseaseModel
from . import cli

@cli.command()
def simplesim_java():
    """Run the simulation."""
    num_ticks = int(os.environ["NUM_TICKS"])
    tick_time = int(os.environ["TICK_TIME"])
    output_file = os.environ["OUTPUT_FILE"]

    print("Loading disease model")
    disease_model = DiseaseModel(os.environ["DISEASE_MODEL_FILE"])

    print("Initializing behavior model")
    behavior_model = SimpleJavaBehaviorModel()

    epicurve = []

    it_1 = range(num_ticks)
    for tick in it_1:
        print("Starting tick %d" % tick)

        state_df = behavior_model.next_state_df
        visit_df = behavior_model.next_visit_df

        print("Computing epicurve.")
        state_count = state_df.groupby("current_state").agg({"pid": len}).pid
        epirow = [state_count.get(i, 0) for i in range(disease_model.n_states)]
        epicurve.append(epirow)


        it_2 = visit_df.groupby("lid")
        it_2 = tqdm(it_2, desc="Transmission step", unit="location")
        visit_outputs = []
        for lid, group in it_2:
            visit_output = disease_model.compute_visit_output(group, behavior_model.attr_names)
            visit_output["lid"] = lid
            visit_outputs.append(visit_output)
        visit_output_df = pd.concat(visit_outputs, axis=0)

        state_df = state_df.set_index("pid", drop=False)

        it_3 = visit_output_df.groupby("pid")
        it_3 = tqdm(it_3, desc="Progression step", unit="person")
        new_states = []
        for pid, group in it_3:
            cur_state = state_df.loc[pid]
            new_state = disease_model.compute_progression_output(cur_state, group, tick_time)
            new_states.append(new_state)
        new_state_df = pd.DataFrame(new_states)

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
