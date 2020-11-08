"""Simple behavior model."""

import os
import time
import logging

import pyarrow as pa
import py4j.java_gateway
import py4j.protocol

from .data_schema import make_visit_output_schema, make_state_schema


def get_gateway():
    """Retry getting gateway until retries are exhausted."""
    max_tries = int(os.environ.get("GATEWAY_CONNECTION_RETRIES", 300))

    logger = logging.getLogger("py4j")
    logger.setLevel(logging.CRITICAL)

    print("Trying to connect to behavior gateway.")
    tries = 0
    while tries < max_tries:
        try:
            gateway = py4j.java_gateway.JavaGateway(eager_load=True)
            print("Successfully connected to behavior gateway.")

            logger.setLevel(logging.WARNING)
            return gateway
        except (py4j.protocol.Py4JNetworkError, OSError):
            time.sleep(1)
            tries += 1
    raise RuntimeError("Couldn't connect to behavior gateway.")


class SimpleJavaBehaviorModel:
    """Simple behavior model."""

    def __init__(self):
        """Initialize."""
        self.attr_names = os.environ["VISUAL_ATTRIBUTES"].strip().split(",")
        self.gateway = None
        self.visit_output_schema = make_visit_output_schema(self.attr_names)
        self.state_schema = make_state_schema()

        self.gateway = get_gateway()

    def __del__(self):
        """Cleanup."""
        self.close()

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

    def close(self):
        """Close the JVM Gateway."""
        if self.gateway is not None:
            self.gateway.entry_point.cleanup()
            self.gateway.shutdown()
            self.gateway.close()

            self.gateway = None
