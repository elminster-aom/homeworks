"""Validate that DB and Communication bus (Kafka) are defined with all
needed resources for our web-monitoring application
"""

import pytest
import src.config as config
import traceback
from src.communication_manager import Communication_manager
from src.store_manager import Store_manager


def test_kafka_resources():
    """Validate that our topic is already created in kafka"""
    assertion = False
    try:
        kafka = Communication_manager()
        kafka.connect_consumer()
    except Exception:
        print(traceback.print_exc())
    else:
        topics_set = kafka.kafka_consumer.topics()
        print(f"List of available topics in Kafka: {topics_set}")
        if config.kafka_topic_name in topics_set:
            assertion = True
    finally:
        kafka.close_consumer()

    # fmt: off
    assert assertion, f"Test failed because our topic '{config.kafka_topic_name}' is not in the list of defined Kafka topics: {topics_set}"
    # fmt: on


def test_postgres_resources_1():
    """Validate that our table is already created as hypertable and it has 2 dimensions in Postgres"""
    assertion = False
    try:
        postgres = Store_manager()
        assertion = postgres.validate_metric_store()
    finally:
        postgres.close()

    # fmt: off
    assert assertion, f"Something wrong with DB definitions, '{config.db_table}' is not a hypertable or does not have two dimension"
    # fmt: on


""" 1. Confirm the debug-output for DB reports right definition for our metrics, e.g. from:
$ ./setup.py
Connecting with DB
Established connection with DB, status code: 1
Connection with DB already established, status code: 1
Enabling TimescaleDB extension, if it doesn't exist
Creating table for metrics (web_health_metrics), if it doesn't exist
Turning 'web_health_metrics' to a hypertable partitioned by 2 dimensions: 'time' and 'web_url', if it doesn't exist
All DB resources were created
Connection with DB already established, status code: 1
Database ready for storing metrics, all resources crated
Information about our table in '_timescaledb_catalog.hypertable':
	RealDictRow([('id', 35), ('schema_name', 'public'), ('table_name', 'web_health_metrics'), ('associated_schema_name', '_timescaledb_internal'), ('associated_table_prefix', '_hyper_35'), ('num_dimensions', 2), ('chunk_sizing_func_schema', '_timescaledb_internal'), ('chunk_sizing_func_name', 'calculate_chunk_interval'), ('chunk_target_size', 0), ('compression_state', 0), ('compressed_hypertable_id', None), ('replication_factor', None)])
Connection with DB was closed

Checks:
* RealDictRow.table_name == web_health_metrics
* RealDictRow.num_dimensions == 2
* ??? Dimension == ('time', 'web_url') 
"""
