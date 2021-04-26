import io
import logging
import psycopg2
from . import config
from psycopg2 import extras

log = logging.getLogger("homeworks")


class Store_manager:
    """Implement the methods for storing the metrics collected by the application"""

    def __init__(self):
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
        self.connect()
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

    def connect(self) -> bool:
        """Establish a permanent connection with DB for storing monitoring metrics
        * Sets `self.db_connect`, object to DB

        Returns:
            bool: Returns True when connection is succesfully established
        """
        # TODO: Implement a more accurate status control, see https://www.psycopg.org/docs/extensions.html#connection-status-constants

        result = False
        if not self.db_connect:
            try:
                log.debug("Connecting with DB")
                self.db_connect = psycopg2.connect(config.db_uri)
            except Exception:
                log.exception("Cannot establish connection with DB")
                raise
            else:
                self.db_connect.autocommit = self.db_autocommit
                log.info(
                    f"Established connection with DB, status code: {self.db_connect.status}"
                )
                result = True
        else:
            log.debug(
                f"Connection with DB already established, status code: {self.db_connect.status}"
            )
            result = True
        return result

    def validate_metric_store(self) -> bool:
        """Vaidate that both TimescaleDB extension and a hypertable for storing monitoring metrics
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

        return result

    def initialize_metrics_store(self):
        """Create both TimescaleDB extension and a hypertable for storing our monitoring metrics"""
        try:
            self.connect()
            with self.db_connect.cursor() as db_cursor:
                log.info("Enabling TimescaleDB extension, if it doesn't exist")
                db_cursor.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE")
                log.info(
                    f"Creating table for metrics ({self.db_table}), if it doesn't exist"
                )
                db_cursor.execute(
                    f"""CREATE TABLE IF NOT EXISTS {self.db_table} (
                            time         TIMESTAMPTZ       NOT NULL,
                            web_url      TEXT              NOT NULL,
                            http_status  SMALLINT          NOT NULL,
                            resp_time    DOUBLE PRECISION  NOT NULL,
                            regex_match  BOOLEAN           NULL
                        )"""
                )
                log.info(
                    f"Turning '{self.db_table}' to a hypertable partitioned by 2 dimensions: 'time' and 'web_url', if it doesn't exist"
                )
                db_cursor.execute(
                    f"""SELECT create_hypertable(
                            '{self.db_table}',
                            'time', 'web_url',
                            {self.hypertable_number_partitions},
                            chunk_time_interval => interval '{self.hypertable_chunk_time_interval}',
                            if_not_exists => TRUE
                        )"""
                )

        except (psycopg2.Error, Exception):
            log.exception("TimescaleDB extension could not be created")
            raise
        else:
            log.info("All DB resources were created")

    @staticmethod
    def clean_values(value: any) -> str:
        """Converts all field values (str, int, float, ...) to str before
        calling copy_from().
        * Workaround: Manually converted `None` to \\N for avoiding
        psycopg2.errors.InvalidTextRepresentation

        Args:
            value (Any): Field value to convert to string

        Returns:
            str: Field value converted to string
        """

        if value:
            return str(value)
        else:
            # Otherwise: psycopg2.errors.InvalidTextRepresentation: invalid input syntax for type boolean: "None"
            return r"\N"

    def insert_metric_copy(self, metrics: list[dict]) -> None:
        """Store a list of dictionary elements (the collected web metrics) in DB
        * Implementation is based on io.StringIO() and psycopg2.cursor.copy_from() basec on:
            Fastest Way to Load Data Into PostgreSQL Using Python,
            https://hakibenita.com/fast-load-data-python-postgresql#copy-data-from-a-string-iterator-with-buffer-size
        * We considered to use mmap, instead io.StringIO(), because it's iterable and Kernel system calls handel file
        data in memory. However, mmap.mmap.read() returns bytes and it's necessary to extend the class for decode them
        to strings
        Args:
            metrics (list[dict]): List of web metrics to store
        """
        # TODO: Analize the viability to substitue io.StringIO() with mmap.mmap()

        log.debug(f"Inserting, in DB, metrics:\n\t{metrics}")
        metrics_stringIO = io.StringIO()
        for metric_dict in metrics:
            metric_csv = ",".join(map(self.clean_values, metric_dict.values())) + "\n"
            # log.debug(f"Convert to CSV and insert in metrics_stringIO: {metric_csv}")
            # TODO: URGENT! Substitute metric_dict.values() by specific calls to the keys, for ensuring the right field's order
            metrics_stringIO.write(metric_csv)

        log.debug(f"metrics_stringIO: {metrics_stringIO.getvalue()}")
        if len(metrics_stringIO.getvalue()) > 0:
            metrics_stringIO.seek(0)

            with self.db_connect.cursor() as db_cursor:
                log.debug(
                    "Copying metrics from metrics_stringIO to DB with db_cursor.copy_from()"
                )
                try:
                    db_cursor.copy_from(metrics_stringIO, self.db_table, sep=",")
                except (psycopg2.Error, Exception):
                    log.exception("Could not copy metrics in DB")
                    raise
                else:
                    log.info("Metrics copied in DB")
                finally:
                    metrics_stringIO.close()
        else:
            log.info("Nothing to copy in DB")
