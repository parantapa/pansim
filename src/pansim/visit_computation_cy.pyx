#cython: infer_types=True
#cython: language_level=3
#distutils: language = c++
"""Visit computation cython version."""

from libc.math cimport pow as cpow
from libcpp.unordered_set cimport unordered_set
from libcpp.vector cimport vector
from numpy cimport float64_t, int8_t, int32_t, int64_t
cimport cython

DEF C_START_EVENT = 1
DEF C_END_EVENT = 0

START_EVENT = 1
END_EVENT = 0

cdef inline float64_t padd(float64_t p, float64_t q):
    """Add the probabilities."""
    return 1.0 - (1.0 - p) * (1.0 - q)


cdef inline float64_t pmul(float64_t p, float64_t n):
    """Return the multiple of the given probabilty."""
    return 1.0 - cpow(1.0 - p, n)


@cython.boundscheck(True)
@cython.wraparound(False)
@cython.cdivision(True)
def compute_visit_output_cy(
        float64_t[:,:,:,:,:,:] transmission_prob not None,
        float64_t[:,:] succeptibility not None,
        float64_t[:,:] infectivity not None,
        float64_t unit_time,
        int64_t[:] e_indices_sorted not None,
        int64_t[:] e_event_visit not None,
        int32_t[:] e_event_time not None,
        int8_t[:] e_event_type not None,
        int8_t[:] v_state not None,
        int8_t[:] v_group not None,
        int8_t[:] v_behavior not None,
        int8_t[:,:] v_attributes not None,
        float64_t[:] vo_inf_prob not None,
        int32_t[:] vo_n_contacts not None,
        int32_t[:,:] vo_attributes not None):
    """Compute the visit results."""
    cdef int64_t n_events = e_indices_sorted.shape[0]
    assert n_events > 0
    assert e_event_visit.shape[0] == n_events
    assert e_event_time.shape[0] == n_events
    assert e_event_type.shape[0] == n_events

    cdef int64_t n_visits = v_state.shape[0]
    assert n_visits > 0
    assert v_group.shape[0] == n_visits
    assert v_behavior.shape[0] == n_visits
    assert v_attributes.shape[1] == n_visits
    assert vo_inf_prob.shape[0] == n_visits
    assert vo_n_contacts.shape[0] == n_visits
    assert vo_attributes.shape[1] == n_visits

    cdef int64_t n_attributes = v_attributes.shape[0]
    assert n_attributes > 0
    assert vo_attributes.shape[0] == n_attributes

    assert unit_time > 0

    cdef int64_t cur_occupancy = 0
    cdef int32_t prev_time = -1
    cdef int32_t cur_time
    cdef int8_t event_type
    cdef unordered_set[int64_t] cur_all_indices
    cdef unordered_set[int64_t] cur_succ_indices
    cdef unordered_set[int64_t] cur_infc_indices
    cdef vector[int64_t] cur_attr_count;

    cur_attr_count.resize(n_attributes, 0)

    cdef int64_t i_event_sorted, i_event, i_visit
    cdef int64_t i_succ, i_infc
    cdef int64_t i_attr, i_present
    cdef float64_t duration
    cdef int64_t ss, sg, sb
    cdef int64_t is_, ig, ib
    cdef int64_t vs, vg
    cdef float64_t prob

    for i_event_sorted in range(n_events):
        i_event = e_indices_sorted[i_event_sorted]
        i_visit = e_event_visit[i_event]
        cur_time = e_event_time[i_event]
        event_type = e_event_type[i_event]

        # Update the infection probabilities
        if prev_time != -1:
            duration = cur_time - prev_time

            if duration > 0.0 and cur_succ_indices.size() > 0 and cur_infc_indices.size() > 0:
                duration = duration / unit_time

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
        if event_type == C_START_EVENT:
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
        else: # event_type == END_EVENT
            for i_attr in range(n_attributes):
                if v_attributes[i_attr, i_visit]:
                    cur_attr_count[i_attr] -= 1
            cur_occupancy -= 1

        # Update the succeptible, infectious user accounting
        vs = v_state[i_visit]
        vg = v_group[i_visit]
        if event_type == C_START_EVENT:
            cur_all_indices.insert(i_visit)
            if succeptibility[vs, vg] > 0.0:
                cur_succ_indices.insert(i_visit)
            if infectivity[vs, vg] > 0.0:
                cur_infc_indices.insert(i_visit)
        else: # event_type == END_EVENT
            cur_all_indices.erase(i_visit)
            if succeptibility[vs, vg] > 0.0:
                cur_succ_indices.erase(i_visit)
            if infectivity[vs, vg] > 0.0:
                cur_infc_indices.erase(i_visit)
