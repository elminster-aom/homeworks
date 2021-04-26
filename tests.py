"""Validate that DB and Communication bus (Kafka) are defined with all
needed resources for our web-monitoring application
"""

import traceback
from src.communication_manager import Communication_manager


def test_kafka_resources():
    try:
        kafak_consumer = Communication_manager()
    except Exception:
        print(traceback.format_exc())
    else:
        print(kafak_consumer.topics())
    finally:
        kafak_consumer.close()


if __name__ == "__main__":
    test_kafka_resources()

""" 1. Confirm the debug-output for DB reports right definition for our metrics, e.g. from:
$ ./setup.py
Connecting with DB
Stablished connection with DB, status code: 1
Connection with DB already stablished, status code: 1
Enabling TimescaleDB extension, if it doesn't exist
Creating table for metrics (web_health_metrics), if it doesn't exist
Turning 'web_health_metrics' to a hypertable partitioned by 2 dimensions: 'time' and 'web_url', if it doesn't exist
All DB resources were created
Connection with DB already stablished, status code: 1
Database ready for storing metrics, all resources crated
Information about our table in '_timescaledb_catalog.hypertable':
	RealDictRow([('id', 35), ('schema_name', 'public'), ('table_name', 'web_health_metrics'), ('associated_schema_name', '_timescaledb_internal'), ('associated_table_prefix', '_hyper_35'), ('num_dimensions', 2), ('chunk_sizing_func_schema', '_timescaledb_internal'), ('chunk_sizing_func_name', 'calculate_chunk_interval'), ('chunk_target_size', 0), ('compression_state', 0), ('compressed_hypertable_id', None), ('replication_factor', None)])
Connection with DB was closed

Checks:
* RealDictRow.table_name == web_health_metrics
* RealDictRow.num_dimensions == 2
* ??? Dimension == ('time', 'web_url') 
"""
