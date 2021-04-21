"""Independet module for inialiting the environment, it has be ran only once (per environment) before anything else
1. It assumes that PosgresSQL is up and running and we have administratitve authorization
2. It assumes that Kafka is up and running and we have administratitve authorization
3. It enables TimescaleDB extension in PostgresSQL
4. It creates a table for storing web_health monitoring
5. It turns previous table in a hypertable partitioned, for storing monitoring metrics
"""

import logging
import psycopg2
import sys
from src.config import Config

log = logging.getLogger(__name__)
# set to DEBUG for early-stage debugging
log.setLevel(logging.INFO)


def init_logging():
    """Initialization of basic logging to console, stdout and stderr, where
    log level INFO goes to stdout and anything else to stderr
    See: https://stackoverflow.com/questions/2302315/how-can-info-and-debug-logging-message-be-sent-to-stdout-and-higher-level-messag
    """

    class IsEqualFilter(logging.Filter):
        def __init__(self, level, name=""):
            logging.Filter.__init__(self, name)
            self.level = level

        def filter(self, record):
            # non-zero return means we log this message
            return 1 if record.levelno == self.level else 0

    class IsNotEqualFilter(logging.Filter):
        def __init__(self, level, name=""):
            logging.Filter.__init__(self, name)
            self.level = level

        def filter(self, record):
            # non-zero return means we log this message
            return 1 if record.levelno != self.level else 0

    logging_handler_out = logging.StreamHandler(sys.stdout)
    logging_handler_out.addFilter(IsEqualFilter(logging.INFO))
    log.addHandler(logging_handler_out)
    logging_handler_err = logging.StreamHandler(sys.stderr)
    logging_handler_err.addFilter(IsNotEqualFilter(logging.INFO))
    log.addHandler(logging_handler_err)
    # Prevent exception logging while emitting
    logging.raiseExceptions = False


def initialize_metrics_store(
    db_uri, db_table, number_partitions=4, chunk_time_interval="1 week"
):
    """Create of both TimescaleDB extension and a table for storing monitoring metrics

    Args:
        db_uri (string): Ful URI (Including: user, password and default database) for connecting to DB
        db_table (string): Name of the DB hypertable where metrics will be stored
        number_partitions (int, optional): Number of partitions for `db_table` . Defaults to 4.
        chunk_time_interval (str, optional): How long in time will chunk metrics data. Defaults to "1 week".
    """
    try:
        db_connect = psycopg2.connect(db_uri)
        with db_connect.cursor() as db_cursor:
            log.info("Creating the TimescaleDB extension")
            db_cursor.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE")
            log.info(f"Creating table for metrics: {db_table}")
            db_cursor.execute(
                f"""CREATE TABLE IF NOT EXISTS {db_table} (
                        time         TIMESTAMPTZ       NOT NULL,
                        web_url      TEXT              NOT NULL,
                        http_status  SMALLINT          NOT NULL,
                        resp_time    DOUBLE PRECISION  NOT NULL,
                        regex_match  BOOLEAN           NULL
                    )"""
            )
            log.info(f"Turn '{db_table}' hypertable partitioned by time and web_url")
            db_cursor.execute(
                f"""SELECT create_hypertable(
                        '{db_table}',
                        'time', 'web_url',
                        {number_partitions},
                        chunk_time_interval => interval '{chunk_time_interval}',
                        if_not_exists => TRUE
                    )"""
            )

    except (Exception, psycopg2.Error):
        logging.exception("TimescaleDB extension could not be crated")
    else:
        db_connect.commit()
        logging.info("Database ready for storing metrics, all resources crated")
    finally:
        if db_connect:
            db_connect.close()


def main():
    """Main pogram"""
    initialize_metrics_store(config.db_uri, config.db_table)


if __name__ == "__main__":
    config = Config()
    init_logging()
    try:
        main()
    except Exception as e:
        logging.exception("Raised exception to main")
