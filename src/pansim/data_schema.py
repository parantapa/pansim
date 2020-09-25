"""PyArrow schema for data exchange."""

import pyarrow as pa


def make_visit_schema(visual_attributes):
    """Return the visit schema."""
    schema = [
        ("lid", pa.int64()),
        ("pid", pa.int64()),
        ("group", pa.int8()),
        ("state", pa.int8()),
        ("behavior", pa.int8()),
        ("start_time", pa.int32()),
        ("end_time", pa.int32()),
    ]

    columns = set(k for k, v in schema)
    for attr in visual_attributes:
        if attr in columns:
            raise ValueError(f"Can't make visit schema: {attr} is already a column")
        columns.add(attr)

        field = (attr, pa.int8())
        schema.append(field)

    return pa.schema(schema)


def make_visit_output_schema(visual_attributes):
    """Return the visit output schema."""
    schema = [
        ("lid", pa.int64()),
        ("pid", pa.int64()),
        ("inf_prob", pa.float64()),
        ("n_contacts", pa.int32()),
    ]

    columns = set(k for k, v in schema)
    for attr in visual_attributes:
        if attr in columns:
            raise ValueError(
                f"Can't make visit output schema: {attr} is already a column"
            )
        columns.add(attr)

        field = (attr, pa.int32())
        schema.append(field)

    return pa.schema(schema)


def make_state_schema():
    """Return the person state schema."""
    schema = [
        ("pid", pa.int64()),
        ("group", pa.int8()),
        ("current_state", pa.int8()),
        ("next_state", pa.int8()),
        ("dwell_time", pa.int32()),
        ("seed", pa.int64()),
    ]

    return pa.schema(schema)
