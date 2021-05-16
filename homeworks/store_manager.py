import psycopg2
from psycopg2 import extras
from . import config
from . import logging_console


log = logging_console.getLogger("homeworks")


class Store_manager:
    """Implement the methods for storing the metrics collected by the monitoring application"""

    def __init__(self) -> None:
        """Default constructor

        Properties:
            db_connect = DB connection
            db_autocommit (bool) = If True, no transaction is handled by the driver and every statement sent to the backend has immediate effect
            db_table (str): Name of the DB hypertable where metrics will be stored
            hypertable_number_partitions (int, optional): Number of partitions for `db_table` . Defaults to 4.
            hypertable_chunk_time_interval (str, optional): How long in time will chunk metrics data. Defaults to "1 week".
        """
        self.db_connect = None
        self.db_autocommit = config.db_autocommit
        self.db_table = config.db_table
        # TODO: Create a tuning-setup config file for the values below
        self.hypertable_number_partitions = 4
        self.hypertable_chunk_time_interval = "1 week"

    def __del__(self) -> None:
        self.close()

    def close(self) -> None:
        """Close the DB connection"""
        if self.db_connect:
            self.db_connect.close()
            self.db_connect = None
            log.info("Connection with DB was closed")

    def connect(self) -> None:
        """Establish a permanent connection with DB for storing monitoring metrics
        * Sets `self.db_connect`, object to DB

        Returns:
            bool: Returns True when connection is successfully established
        """
        if self.db_connect:
            # TODO: Implement a more accurate status control, see https://www.psycopg.org/docs/extensions.html#connection-status-constants
            log.debug(
                f"DB connection already established, status code: {self.db_connect.status}"
            )
        else:
            log.debug("Connecting with DB")
            try:
                self.db_connect = psycopg2.connect(config.db_uri)
                self.db_connect.autocommit = self.db_autocommit
            except Exception:
                log.exception("Cannot establish connection with DB")
                raise
            else:
                log.debug(
                    f"Established connection with DB, status code: {self.db_connect.status}"
                )

    def validate_metric_store(self) -> bool:
        """Validate that both TimescaleDB extension and a hypertable for storing monitoring metrics
        are properly created

        Returns:
            bool: Return True when DB is ready for storing our metrics
        """
        result = False
        hypertable_result = None
        try:
            self.connect()
            with self.db_connect.cursor(
                cursor_factory=extras.RealDictCursor
            ) as db_cursor:
                # Check the metainformation of our table in the database catalog
                db_cursor.execute(
                    f"SELECT * FROM _timescaledb_catalog.hypertable WHERE table_name='{self.db_table}'"
                )
                hypertable_result = db_cursor.fetchone()
        except (psycopg2.Error, Exception):
            log.exception(
                "DB catalog (_timescaledb_catalog.hypertable) could not be accessed"
            )
            raise
        else:
            if hypertable_result and hypertable_result["num_dimensions"] == 2:
                log.info(f"Database ready for storing metrics, all resources created")
                log.info(
                    f"Extra details in catalog (_timescaledb_catalog.hypertable):\n\t{hypertable_result}"
                )
                result = True
            else:
                log.error(
                    f"Something wrong with DB definitions, '{self.db_table}' is not a hypertable or does not have two dimensions"
                )
        finally:
            self.close()
            return result

    def initialize_metrics_store(self) -> None:
        """Create both TimescaleDB extension and a hypertable for storing our monitoring metrics"""
        sql_enable_timescaleDB = "CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE"
        sql_create_table = f"""CREATE TABLE IF NOT EXISTS {self.db_table} (
                                time         TIMESTAMPTZ       NOT NULL,
                                web_url      TEXT              NOT NULL,
                                http_status  SMALLINT          NOT NULL,
                                resp_time    DOUBLE PRECISION  NOT NULL,
                                regex_match  BOOLEAN           NULL
                               )"""
        sql_convert_to_hypertable = f"""SELECT create_hypertable(
                                        '{self.db_table}',
                                        'time', 'web_url',
                                        {self.hypertable_number_partitions},
                                        chunk_time_interval => interval '{self.hypertable_chunk_time_interval}',
                                        if_not_exists => TRUE
                                    )"""
        try:
            self.connect()
            with self.db_connect.cursor() as db_cursor:
                log.info("Enabling TimescaleDB extension, if it doesn't exist")
                db_cursor.execute(sql_enable_timescaleDB)
                log.info(
                    f"Creating table for metrics ({self.db_table}), if it doesn't exist"
                )
                db_cursor.execute(sql_create_table)
                log.info(
                    f"Turning '{self.db_table}' to a hypertable partitioned by 2 dimensions: 'time' and 'web_url', if it doesn't exist"
                )
                db_cursor.execute(sql_convert_to_hypertable)
        except (psycopg2.Error, Exception):
            log.exception("TimescaleDB extension could not be created")
            raise
        else:
            log.info("All DB resources were created")
        finally:
            self.close()

    def insert_metrics_batch(self, metrics: list[dict]) -> None:
        """Store a list of dictionary elements (the collected web metrics) in DB
        Implementation is based on direct inserts on DB

        Args:
            metrics (list[dict]): List of web metrics to store
        """
        if len(metrics) > 0:
            log.debug(f"Inserting, in DB, metrics:\n\t{metrics}")
            sql_insert_string = f"""INSERT INTO {self.db_table} VALUES (
                                    %(time)s,
                                    %(web_url)s,
                                    %(http_status)s,
                                    %(resp_time)s,
                                    %(regex_match)s
                                )"""
            try:
                self.connect()
                with self.db_connect.cursor() as db_cursor:
                    psycopg2.extras.execute_batch(db_cursor, sql_insert_string, metrics)
            except (psycopg2.Error, Exception):
                log.exception("Could not insert metrics in DB")
                raise
            else:
                log.info("Metrics inserted in DB")
        else:
            log.info("Nothing to insert in DB")
