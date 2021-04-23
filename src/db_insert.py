"""See: Fastest Way to Load Data Into PostgreSQL Using Python,
https://hakibenita.com/fast-load-data-python-postgresql#copy-data-from-a-string-iterator-with-buffer-size
"""

import io
import json
import logging
import psycopg2
from psycopg2 import extras

log = logging.getLogger("homeworks")


class Metrics_send:
    def __init__(
        self, db_uri: str, db_table: str, db_buffer_path: str, db_autocomit: bool = True
    ) -> None:
        self.db_connect = psycopg2.connect(db_uri)
        self.db_table = db_table
        self.db_buffer_path = db_buffer_path
        # When True, every executed command takes effect immediately.
        self.db_connect.autocommit = db_autocomit

    def __del__(self) -> None:
        self.close()

    def close(self) -> None:
        if self.db_connect:
            self.db_connect.close()

    @staticmethod
    def clean_values(value) -> str:
        if value:
            return str(value)
        else:
            # Otherwise: psycopg2.errors.InvalidTextRepresentation: invalid input syntax for type boolean: "None"
            return r"\N"

    def insert_metric_copy(self, metrics: list[str]) -> None:
        metrics_stringIO = io.StringIO()
        for metric_json in metrics:
            metric_dict = json.loads(metric_json)
            metrics_stringIO.write(
                "|".join(map(self.clean_values, metric_dict.values())) + "\n"
            )
        metrics_stringIO.seek(0)
        log.debug(f"metric_str: {metrics_stringIO.read()}")
        metrics_stringIO.seek(0)

        with self.db_connect.cursor() as db_cursor:
            db_cursor.copy_from(metrics_stringIO, self.db_table, sep="|")
