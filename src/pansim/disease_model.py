"""PanSim Disease Model."""

import random

import toml
import numpy as np

from .sampler import FixedSampler, CategoricalSampler
# from .visit_computation_py import (
#         compute_visit_output_py as compute_visit_output,
#         START_EVENT,
#         END_EVENT
# )
from .visit_computation_cy import (
        compute_visit_output_cy as compute_visit_output,
        START_EVENT,
        END_EVENT
)

# from line_profiler import LineProfiler
# profile = LineProfiler()


SEED_MIN = np.iinfo(np.int64).min
SEED_MAX = np.iinfo(np.int64).max
NULL_STATE = -1
NULL_DWELL_TIME = -1

def psum(ps, axis=-1):
    """Add the probabilites."""
    ps = 1.0 - ps
    ps = np.product(ps, axis=axis)
    ps = 1.0 - ps
    return ps


class DiseaseModel:
    """The disease model structure."""

    def __init__(self, fname=None, model_dict=None):
        """Initialize."""
        if (fname is None) == (model_dict is None):
            raise ValueError(
                "One and only one of 'fname' or 'model_dict' must be provided."
            )

        if fname is not None:
            with open(fname, "rt") as fobj:
                model_dict = toml.load(fobj)

        self.fname = fname
        self.model_dict = model_dict

        self.name_state = {s: i for i, s in enumerate(model_dict["states"])}
        self.name_group = {g: i for i, g in enumerate(model_dict["groups"])}
        self.name_behavior = {b: i for i, b in enumerate(model_dict["behaviors"])}

        self.n_states = len(model_dict["states"])
        self.n_groups = len(model_dict["groups"])
        self.n_behaviors = len(model_dict["behaviors"])

        self.unit_time = float(model_dict["unit_time"])
        self.exposed_state = self.name_state[model_dict["exposed_state"]]

        self.succeptibility = self._compute_succeptibility()
        # print(self.succeptibility)
        self.infectivity = self._compute_infectivity()
        # print(self.infectivity)
        self.transmission_prob = self._compute_transmission_prob()
        # print(self.transmission_prob)

        self.progression = self._compute_progression()
        self.dwell_time = self._compute_dwell_time()

    # def __del__(self):
    #     profile.dump_stats("lineprof.lprof")

    def _compute_succeptibility(self):
        """Compute the succeptibility matrix."""
        shape = (self.n_states, self.n_groups)
        succeptibility = np.zeros(shape, dtype=np.float64)

        states = self.model_dict["states"]
        groups = self.model_dict["groups"]
        sdict = self.model_dict["succeptibility"]

        for state, sname in enumerate(states):
            for group, gname in enumerate(groups):
                try:
                    succeptibility[state][group] = sdict[sname][gname]
                except KeyError:
                    pass

        return succeptibility

    def _compute_infectivity(self):
        """Compute the infectivity matrix."""
        shape = (self.n_states, self.n_groups)
        infectivity = np.zeros(shape, dtype=np.float64)

        states = self.model_dict["states"]
        groups = self.model_dict["groups"]
        idict = self.model_dict["infectivity"]

        for state, sname in enumerate(states):
            for group, gname in enumerate(groups):
                try:
                    infectivity[state][group] = idict[sname][gname]
                except KeyError:
                    pass

        return infectivity

    def _compute_transmission_prob(self):
        """Populate self.transmission_prob."""
        shape = (
            self.n_states,
            self.n_groups,
            self.n_behaviors,
            self.n_states,
            self.n_groups,
            self.n_behaviors,
        )
        transmission_prob = np.zeros(shape, dtype=np.float64)

        states = self.model_dict["states"]
        groups = self.model_dict["groups"]
        behaviors = self.model_dict["behaviors"]

        sdict = self.model_dict["succeptibility"]
        idict = self.model_dict["infectivity"]
        bdict = self.model_dict["behavior_modifier"]

        for state_s, sname_s in enumerate(states):
            for group_s, gname_s in enumerate(groups):
                for behavior_s, bname_s in enumerate(behaviors):
                    for state_i, sname_i in enumerate(states):
                        for group_i, gname_i in enumerate(groups):
                            for behavior_i, bname_i in enumerate(behaviors):

                                try:
                                    succ = sdict[sname_s][gname_s]
                                except KeyError:
                                    succ = 0.0

                                try:
                                    infc = idict[sname_i][gname_i]
                                except KeyError:
                                    infc = 0.0

                                try:
                                    bmod = bdict[bname_s][bname_i]
                                except KeyError:
                                    bmod = 1.0

                                prob = succ * infc * bmod
                                transmission_prob[state_s][group_s][behavior_s][
                                    state_i
                                ][group_i][behavior_i] = prob

                                # if prob > 0:
                                #     print(sname_s, gname_s, bname_s, sname_i, gname_i, bname_i, prob)


        return transmission_prob

    def _compute_progression(self):
        """Return the progression data structure."""
        groups = self.model_dict["groups"]
        pdict = self.model_dict["progression"]

        progression = {}
        for sname, v1 in pdict.items():
            state = self.name_state[sname]
            progression[state] = {}

            for gname in groups:
                v2 = v1[gname]
                group = self.name_group[gname]

                dist = {self.name_state[k]: v for k, v in v2.items()}
                progression[state][group] = CategoricalSampler(dist)
        return progression

    def _compute_distibutions(self):
        """Return the defined distributions."""
        ddict = self.model_dict["distribution"]

        distributions = {}
        for dname, v1 in ddict.items():
            if v1["dist"] == "categorical":
                d = zip(v1["categories"], v1["p"])
                d = dict(d)
                d = CategoricalSampler(d)
                distributions[dname] = d
            elif v1["dist"] == "fixed":
                d = v1["value"]
                d = FixedSampler(d)
                distributions[dname] = d
            else:
                raise ValueError("Only distributions supported are: categorical, fixed")

        # print(distributions)
        return distributions

    def _compute_dwell_time(self):
        """Return the dwell time data structure."""
        groups = self.model_dict["groups"]
        ddict = self.model_dict["dwell_time"]

        distributions = self._compute_distibutions()
        dwell_time = {}
        for csname, v1 in ddict.items():
            cs = self.name_state[csname]
            dwell_time[cs] = {}
            for gname in groups:
                v2 = v1[gname]
                g = self.name_group[gname]
                dwell_time[cs][g] = {}
                for nsname, dname in v2.items():
                    ns = self.name_state[nsname]
                    dwell_time[cs][g][ns] = distributions[dname]

        # print(dwell_time)
        return dwell_time

    #@profile
    def compute_visit_output(self, visits, visual_attributes, lid):
        """Compute the visit results."""
        # pd.set_option("display.max_rows", None, "display.max_columns", None)
        # pd.options.display.width = 0
        # print(visits.reset_index())

        n_visits = len(visits)
        n_attributes = len(visual_attributes)

        transmission_prob = self.transmission_prob
        succeptibility = self.succeptibility
        infectivity = self.infectivity
        unit_time = self.unit_time

        e_event_visit = np.hstack([
            np.arange(n_visits, dtype=np.int64),
            np.arange(n_visits, dtype=np.int64)
        ])
        e_event_time = np.hstack([
            visits.start_time.to_numpy(dtype=np.int32),
            visits.end_time.to_numpy(dtype=np.int32)
        ])
        e_event_type = np.hstack([
            np.full(n_visits, START_EVENT, dtype=np.int8),
            np.full(n_visits, END_EVENT, dtype=np.int8),
        ])
        e_indices_sorted = np.lexsort([e_event_type, e_event_time])

        v_state = visits.state.to_numpy(dtype=np.int8)
        v_group = visits.group.to_numpy(dtype=np.int8)
        v_behavior = visits.behavior.to_numpy(dtype=np.int8)
        
        v_attributes = [visits[attr].to_numpy(dtype=np.int8) for attr in visual_attributes]
        v_attributes = np.vstack(v_attributes)

        vo_inf_prob = np.zeros(n_visits, dtype=np.float64)
        vo_n_contacts = np.zeros(n_visits, dtype=np.int32)
        vo_attributes = np.zeros((n_attributes, n_visits), dtype=np.int32)

        compute_visit_output(
            transmission_prob,
            succeptibility,
            infectivity,
            unit_time,
            e_indices_sorted,
            e_event_visit,
            e_event_time,
            e_event_type,
            v_state,
            v_group,
            v_behavior,
            v_attributes,
            vo_inf_prob,
            vo_n_contacts,
            vo_attributes
        )

        # if np.count_nonzero(vo_inf_prob) > 0:
        #     print(np.count_nonzero(vo_inf_prob)

        v_pid = visits.pid.to_numpy(dtype=np.int64)
        v_lid = np.full(n_visits, lid, dtype=np.int64)

        visit_outputs = {
            "pid": v_pid,
            "lid": v_lid,
            "inf_prob": vo_inf_prob,
            "n_contacts": vo_n_contacts,
        }
        for i_attr, attr in enumerate(visual_attributes):
            visit_outputs[attr] = vo_attributes[i_attr, :]

        return visit_outputs

    # @profile
    def compute_progression_output(self, state, visit_outputs, tick_time):
        """Compute the progression outputs."""
        (pid, group, current_state, next_state, dwell_time, seed) = state
        # if current_state != 0:
        #     print(state)

        random.seed(seed)

        # If we are not already in transition
        if dwell_time == NULL_DWELL_TIME:
            # Compute the cumulative infection probability
            inf_p = visit_outputs.inf_prob.to_numpy()
            inf_p = psum(inf_p)

            # Check if we got exposed
            if inf_p > 0:
                # print(inf_p)
                p = random.random()
                if p < inf_p:
                    current_state = self.exposed_state
                    dwell_time = NULL_DWELL_TIME
                    next_state = NULL_STATE

        # If we are not already in transition
        if dwell_time == NULL_DWELL_TIME:
            # Check if there is a transition defined for the current state
            if current_state in self.progression:
                next_state = self.progression[current_state][group].sample()
                dwell_time = self.dwell_time[current_state][group][next_state].sample()

        # If we are in transition
        if dwell_time != NULL_DWELL_TIME:
            if dwell_time > 0:
                dwell_time = dwell_time - tick_time
                if dwell_time < 0:
                    dwell_time = 0
            else:
                current_state = next_state
                dwell_time = NULL_DWELL_TIME
                next_state = NULL_STATE

        # Get a new seed
        seed = random.randint(SEED_MIN, SEED_MAX)

        new_state = (pid, group, current_state, next_state, dwell_time, seed)
        # if current_state != 0:
        #     print(new_state)
        return new_state
