"""Visit computation pure python version."""

START_EVENT = 1
END_EVENT = 0


def padd(p, q):
    """Add the probabilities."""
    return 1.0 - (1.0 - p) * (1.0 - q)


def pmul(p, n):
    """Return the multiple of the given probabilty."""
    return 1.0 - (1.0 - p) ** n


def compute_visit_output_py(
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
    vo_attributes,
):
    """Compute the visit results."""
    n_events = e_indices_sorted.shape[0]
    assert n_events > 0
    assert e_event_visit.shape[0] == n_events
    assert e_event_time.shape[0] == n_events
    assert e_event_type.shape[0] == n_events

    n_visits = v_state.shape[0]
    assert n_visits > 0
    assert v_group.shape[0] == n_visits
    assert v_behavior.shape[0] == n_visits
    assert v_attributes.shape[1] == n_visits
    assert vo_inf_prob.shape[0] == n_visits
    assert vo_n_contacts.shape[0] == n_visits
    assert vo_attributes.shape[1] == n_visits

    n_attributes = v_attributes.shape[0]
    assert n_attributes > 0
    assert vo_attributes.shape[0] == n_attributes

    assert unit_time > 0

    cur_occupancy = 0
    prev_time = -1
    cur_all_indices = set()
    cur_succ_indices = set()
    cur_infc_indices = set()
    cur_attr_count = [0] * n_attributes

    for i_event_sorted in range(n_events):
        i_event = e_indices_sorted[i_event_sorted]
        i_visit = e_event_visit[i_event]
        cur_time = e_event_time[i_event]
        event_type = e_event_type[i_event]

        # Update the infection probabilities
        if prev_time != -1:
            duration = cur_time - prev_time

            if duration > 0.0 and cur_succ_indices and cur_infc_indices:
                duration = float(duration) / unit_time

                for i_succ in cur_succ_indices:
                    ss = v_state[i_succ]
                    sg = v_group[i_succ]
                    sb = v_behavior[i_succ]

                    for i_infc in cur_infc_indices:
                        is_ = v_state[i_infc]
                        ig = v_group[i_infc]
                        ib = v_behavior[i_infc]

                        prob = transmission_prob[ss, sg, sb, is_, ig, ib]
                        prob = pmul(prob, duration)
                        vo_inf_prob[i_succ] = padd(vo_inf_prob[i_succ], prob)

        # Update visual attribute accounting
        if event_type == START_EVENT:
            # The incoming agent sees everyone
            for i_attr in range(n_attributes):
                vo_attributes[i_attr, i_visit] = cur_attr_count[i_attr]
            vo_n_contacts[i_visit] = cur_occupancy

            # Every present agent sees incoming agent
            for i_attr in range(n_attributes):
                if v_attributes[i_attr, i_visit]:
                    for i_present in cur_all_indices:
                        vo_attributes[i_attr, i_present] += 1
            for i_present in cur_all_indices:
                vo_n_contacts[i_present] += 1

            # Update the visual attribute count
            for i_attr in range(n_attributes):
                if vo_attributes[i_attr, i_visit]:
                    cur_attr_count[i_attr] += 1
            cur_occupancy += 1
        else:  # event_type == END_EVENT
            for i_attr in range(n_attributes):
                if v_attributes[i_attr, i_visit]:
                    cur_attr_count[i_attr] -= 1
            cur_occupancy -= 1

        # Update the succeptible, infectious user accounting
        vs = v_state[i_visit]
        vg = v_group[i_visit]
        if event_type == START_EVENT:
            cur_all_indices.add(i_visit)
            if succeptibility[vs, vg] > 0.0:
                cur_succ_indices.add(i_visit)
            if infectivity[vs, vg] > 0.0:
                cur_infc_indices.add(i_visit)
        else:  # event_type == END_EVENT
            cur_all_indices.remove(i_visit)
            if succeptibility[vs, vg] > 0.0:
                cur_succ_indices.remove(i_visit)
            if infectivity[vs, vg] > 0.0:
                cur_infc_indices.remove(i_visit)

        prev_time = cur_time
