"""Simple behavior model."""

import os

import pyarrow as pa
from py4j.java_gateway import JavaGateway

from .data_schema import make_visit_output_schema, make_state_schema

class SimpleJavaBehaviorModel:
    """Simple behavior model."""

    def __init__(self):
        """Initialize."""
        self.attr_names = os.environ["VISUAL_ATTRIBUTES"].strip().split(",")
        self.gateway = JavaGateway()
        self.visit_output_schema = make_visit_output_schema(self.attr_names)
        self.state_schema = make_state_schema()

    @property
    def next_state_df(self):
        """Return the next state df from the server."""
        next_state_df_raw = self.gateway.entry_point.getNextStateDataFrame()
        df = pa.ipc.open_file(next_state_df_raw).get_batch(0).to_pandas()
        print("Received next state dataframe with %d rows" % len(df))
        return df

    @property
    def next_visit_df(self):
        """Return the next visit df from the server."""
        next_visit_df_raw = self.gateway.entry_point.getNextVisitDataFrame()
        df = pa.ipc.open_file(next_visit_df_raw).get_batch(0).to_pandas()
        print("Received next visit dataframe with %d rows" % len(df))
        return df

    def run_behavior_model(self, cur_state_df, visit_output_df):
        """Run the behavior model."""
        print("Sending current state dataframe with %d rows" % len(cur_state_df))
        print("Sending visit output dataframe with %d rows" % len(visit_output_df))

        sink = pa.BufferOutputStream()
        writer = pa.ipc.new_file(sink, self.state_schema)
        batch = pa.record_batch(cur_state_df, schema=self.state_schema)
        writer.write_batch(batch)
        writer.close()
        cur_state_df_raw = sink.getvalue().to_pybytes()

        sink = pa.BufferOutputStream()
        writer = pa.ipc.new_file(sink, self.visit_output_schema)
        batch = pa.record_batch(visit_output_df, schema=self.visit_output_schema)
        writer.write_batch(batch)
        writer.close()
        visit_output_df_raw = sink.getvalue().to_pybytes()

        self.gateway.entry_point.runBehaviorModel(cur_state_df_raw, visit_output_df_raw)
