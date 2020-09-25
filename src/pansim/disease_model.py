"""PanSim Disease Model."""

import random

import toml
import numpy as np
import pandas as pd

from .sampler import FixedSampler, CategoricalSampler

SEED_MIN = np.iinfo(np.int64).min
SEED_MAX = np.iinfo(np.int64).max
NULL_STATE = -1
NULL_DWELL_TIME = -1


def padd(p, q):
    """Add the probabilities."""
    return 1.0 - (1.0 - p) * (1.0 - q)


def psum(ps, axis=-1):
    """Add the probabilites."""
    ps = 1.0 - ps
    ps = np.product(ps, axis=axis)
    ps = 1.0 - ps
    return ps


def pmul(p, n):
    """Return the multiple of the given probabilty."""
    return 1.0 - (1.0 - p) ** n


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

        self.succeptable_states = [self.name_state[s] for s in model_dict["succeptibility"]]
        self.infectious_states = [self.name_state[s] for s in model_dict["infectivity"]]

        self.succeptable_state_index = {s: i for i, s in enumerate(self.succeptable_states)}
        self.infectious_state_index = {s: i for i, s in enumerate(self.infectious_states)}

        self.n_succeptable_states = len(self.succeptable_states)
        self.n_infectious_states = len(self.infectious_states)

        self.unit_time = model_dict["unit_time"]
        self.exposed_state = self.name_state[model_dict["exposed_state"]]

        self.transmission_prob = self._compute_t_prob()
        self.progression = self._compute_progression()
        self.dwell_time = self._compute_dwell_time()

    def _compute_t_prob(self):
        """Populate self.transmission_prob."""
        shape = (
            self.n_succeptable_states,
            self.n_groups,
            self.n_behaviors,
            self.n_infectious_states,
            self.n_groups,
            self.n_behaviors,
        )
        transmission_prob = np.zeros(shape, dtype=np.float64)

        for ss_i in range(self.n_succeptable_states):
            for is_i in range(self.n_infectious_states):
                for sg_i in range(self.n_groups):
                    for ig_i in range(self.n_groups):
                        for sb_i in range(self.n_behaviors):
                            for ib_i in range(self.n_behaviors):

                                ss_name = self.model_dict["states"][self.succeptable_states[ss_i]]
                                is_name = self.model_dict["states"][self.infectious_states[is_i]]
                                sg_name = self.model_dict["groups"][sg_i]
                                ig_name = self.model_dict["groups"][ig_i]
                                sb_name = self.model_dict["behaviors"][sb_i]
                                ib_name = self.model_dict["behaviors"][ib_i]

                                try:
                                    succeptibility = self.model_dict["succeptibility"][ss_name][sg_name]
                                except KeyError:
                                    succeptibility = 0.0

                                try:
                                    infectivity = self.model_dict["infectivity"][is_name][ig_name]
                                except KeyError:
                                    infectivity = 0.0

                                try:
                                    behavior_modifier = self.model_dict["behavior_modifier"][sb_name][ib_name]
                                except KeyError:
                                    behavior_modifier = 1.0

                                prob = succeptibility * infectivity * behavior_modifier
                                transmission_prob[ss_i][sg_i][sb_i][is_i][ig_i][ib_i] = prob

        return transmission_prob

    def _compute_progression(self):
        """Return the progression data structure."""
        progression = {}
        for sname, v1 in self.model_dict["progression"].items():
            state = self.name_state[sname]
            progression[state] = {}

            for gname in self.model_dict["groups"]:
                v2 = v1[gname]
                group = self.name_group[gname]

                dist = {self.name_state[k]: v for k, v in v2.items()}
                progression[state][group] = CategoricalSampler(dist)
        return progression

    def _compute_distibutions(self):
        """Return the defined distributions."""
        distributions = {}
        for dname, v1 in self.model_dict["distribution"].items():
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
        return distributions

    def _compute_dwell_time(self):
        """Return the dwell time data structure."""
        distributions = self._compute_distibutions()
        dwell_time = {}
        for csname, v1 in self.model_dict["dwell_time"].items():
            cs = self.name_state[csname]
            dwell_time[cs] = {}
            for gname in self.model_dict["groups"]:
                v2 = v1[gname]
                g = self.name_group[gname]
                dwell_time[cs][g] = {}
                for nsname, dname in v2.items():
                    ns = self.name_state[nsname]
                    dwell_time[cs][g][ns] = distributions[dname]
        return dwell_time

    def compute_visit_output(self, visits, visual_attributes):
        """Compute the visit results."""
        v_state = visits.state
        v_group = visits.group
        v_behavior = visits.behavior

        v_attr = {attr: visits[attr] for attr in visual_attributes}

        START, END = 1, 0
        events = []
        for index, (start, end) in enumerate(zip(visits.start_time, visits.end_time)):
            events.append((start, START, index))
            events.append((end, END, index))
        events.sort()

        n_visits = len(visits)

        cur_all_indexes = set()
        cur_succeptible_indexes = set()
        cur_infectious_indexes = set()
        cur_attr_count = {attr: 0 for attr in visual_attributes}
        cur_occupancy = 0
        n_contacts = np.zeros(n_visits, dtype=np.int32)
        attr_seen = {
            attr: np.zeros(n_visits, dtype=np.int32) for attr in visual_attributes
        }
        inf_prob = np.zeros(n_visits, dtype=np.float64)
        prev_time = None
        for cur_time, event_type, index in events:
            # Update the infection probabilites
            if prev_time is not None:
                duration = cur_time - prev_time

                if duration > 0 and cur_succeptible_indexes and cur_infectious_indexes:
                    duration = float(duration) / self.unit_time

                    # Increase the infection probability of every succeptable person
                    # Once per infectious person
                    for s_index in cur_succeptible_indexes:
                        ss_i = self.succeptable_state_index[v_state.iat[s_index]]
                        sg_i = v_group.iat[s_index]
                        sb_i = v_behavior.iat[s_index]

                        for i_row in cur_infectious_indexes:
                            is_i = self.infectious_state_index[v_state.iat[i_row]]
                            ig_i = v_group.iat[i_row]
                            ib_i = v_behavior.iat[i_row]

                            p = self.transmission_prob[ss_i][sg_i][sb_i][is_i][ig_i][
                                ib_i
                            ]
                            p = pmul(p, duration)
                            inf_prob[s_index] = padd(inf_prob[s_index], p)

            if event_type == START:
                for attr in visual_attributes:
                    attr_seen[attr][index] = cur_attr_count[attr]
                n_contacts[index] = cur_occupancy

                for attr in visual_attributes:
                    if v_attr[attr].iat[index]:
                        for cindex in cur_all_indexes:
                            attr_seen[attr][cindex] += 1
                for cindex in cur_all_indexes:
                    n_contacts[cindex] += 1

                cur_all_indexes.add(index)
                s = v_state.iat[index]
                if s in self.succeptable_state_index:
                    cur_succeptible_indexes.add(index)
                if s in self.infectious_state_index:
                    cur_infectious_indexes.add(index)

                for attr in visual_attributes:
                    if v_attr[attr].iat[index]:
                        cur_attr_count[attr] += 1
                cur_occupancy += 1
            else:  # event_type == END
                cur_all_indexes.remove(index)
                cur_succeptible_indexes.discard(index)
                cur_infectious_indexes.discard(index)

                for attr in visual_attributes:
                    if v_attr[attr].iat[index]:
                        cur_attr_count[attr] -= 1
                cur_occupancy -= 1

            prev_time = cur_time

        visit_outputs = {
            "pid": visits.pid,
            "inf_prob": inf_prob,
            "n_contacts": n_contacts,
        }
        for attr in visual_attributes:
            attr_seen_col = attr_seen[attr]
            visit_outputs[attr] = attr_seen_col
        visit_outputs = pd.DataFrame(visit_outputs, index=visits.index)

        return visit_outputs

    def compute_progression_output(self, state, visit_outputs, tick_time):
        """Compute the progression outputs."""
        pid = state.pid
        group = state.group
        current_state = state.current_state
        next_state = state.next_state
        dwell_time = state.dwell_time
        seed = state.seed

        random.seed(seed)

        # If we are not already in transition
        if dwell_time == NULL_DWELL_TIME:
            # Compute the cumulative infection probability
            inf_p = psum(visit_outputs.inf_prob.to_numpy())

            # Check if we got exposed
            if inf_p > 0:
                p = random.random()
                if p < inf_p:
                    current_state = self.exposed_state
                    dwell_time = NULL_DWELL_TIME
                    next_state = NULL_STATE

            # Check if there is a transition defined for the current state
            if current_state in self.progression:
                next_state = self.progression[current_state][group].sample()
                dwell_time = self.dwell_time[current_state][group][next_state].sample()

        # If we are in transition
        if dwell_time >= 0:
            if dwell_time > 0:
                dwell_time = min(dwell_time - tick_time, 0)
            else:
                current_state = next_state
                dwell_time = NULL_DWELL_TIME
                next_state = NULL_STATE

        # Get a new seed
        seed = random.randint(SEED_MIN, SEED_MAX)

        new_state = [pid, group, current_state, next_state, dwell_time, seed]
        return pd.Series(
            new_state, index=state.index, dtype=state.dtype, name=state.name
        )
