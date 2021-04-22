#!/usr/bin/env python3
"""Independet module for inialiting the environment, it has be ran only once (per environment) before anything else
1. It assumes that PosgresSQL is up and running and we have administratitve authorization
2. It assumes that Kafka is up and running and we have administratitve authorization
3. It enables TimescaleDB extension in PostgresSQL
4. It creates a table for storing web_health monitoring
5. It turns previous table in a hypertable partitioned, for storing monitoring metrics
"""

import logging
import psycopg2
from psycopg2 import extras
import src.logging_console as logging_console
from src.config import Config

log = logging.getLogger(__name__)


class SetupError(Exception):
    """Minimal exception class for raising controlled errors"""

    pass


def initialize_metrics_store(
    db_uri, db_table, number_partitions=4, chunk_time_interval="1 week"
):
    """Create of both TimescaleDB extension and a table for storing monitoring metrics

    Args:
        db_uri (string): Ful URI (Including: user, password and default database) for connecting to DB
        db_table (string): Name of the DB hypertable where metrics will be stored
        number_partitions (int, optional): Number of partitions for `db_table` . Defaults to 4.
        chunk_time_interval (str, optional): How long in time will chunk metrics data. Defaults to "1 week".
    Raises:
        SetupError: If DB resources are not properly created
    """

    try:
        db_connect = psycopg2.connect(db_uri)
        with db_connect.cursor(cursor_factory=extras.RealDictCursor) as db_cursor:
            log.info("- Enabling TimescaleDB extension")
            db_cursor.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE")
            log.info(f"- Creating table for metrics: {db_table}")
            db_cursor.execute(
                f"""CREATE TABLE IF NOT EXISTS {db_table} (
                        time         TIMESTAMPTZ       NOT NULL,
                        web_url      TEXT              NOT NULL,
                        http_status  SMALLINT          NOT NULL,
                        resp_time    DOUBLE PRECISION  NOT NULL,
                        regex_match  BOOLEAN           NULL
                    )"""
            )
            log.info(
                f"- Turning '{db_table}' to a hypertable partitioned by 'time' and 'web_url'"
            )
            db_cursor.execute(
                f"""SELECT create_hypertable(
                        '{db_table}',
                        'time', 'web_url',
                        {number_partitions},
                        chunk_time_interval => interval '{chunk_time_interval}',
                        if_not_exists => TRUE
                    )"""
            )

            db_cursor.execute(
                f"SELECT * FROM _timescaledb_catalog.hypertable WHERE table_name='{db_table}'"
            )
            # Check in database catalog the metainformation of our table
            hypertable_result = db_cursor.fetchone()

    except (Exception, psycopg2.Error):
        log.exception("TimescaleDB extension could not be crated")
    else:
        db_connect.commit()
    finally:
        if db_connect:
            db_connect.close()

    log.debug(
        f"Information about our table in '_timescaledb_catalog.hypertable':\n\t{hypertable_result}"
    )
    if (hypertable_result == None) or (hypertable_result["num_dimensions"] != 2):
        raise SetupError(
            f"Something wrong with previous definitions, '{db_table}' is not a hypertable or does not have two dimension"
        )
    else:
        log.info("Database ready for storing metrics, all resources crated")


def main():
    """Main pogram"""
    config = Config()
    initialize_metrics_store(config.db_uri, config.db_table)


if __name__ == "__main__":
    logging_console.init_logging()
    log.setLevel(logging.INFO)  # set to DEBUG for early-stage debugging

    try:
        main()
    except Exception as e:
        log.exception("Raised exception to main")
