"""See: Fastest Way to Load Data Into PostgreSQL Using Python,
https://hakibenita.com/fast-load-data-python-postgresql#copy-data-from-a-string-iterator-with-buffer-size
"""

import json
import logging
import mmap
import psycopg2
from psycopg2 import extras

log = logging.getLogger("homeworks")


class Text_mmap(mmap.mmap):
    def __init__(self, fileno, length):
        mmap.mmap.__init__(self)
        self.mmap = mmap.mmap(fileno, length)

    def read(self, reading_caracters=0) -> str:
        # We asume UTF-8, therefore 4 bytes per caracter
        bytes_data = self.mmap.read(reading_caracters * 4)
        return bytes_data.decode

    def readline(self) -> None:
        bytes_data = self.mmap.readline()
        return bytes_data.decode

    def write(self, text_line) -> int:
        print(text_line)
        bytes_wroten = self.mmap.write(str.encode(text_line))
        return bytes_wroten


from typing import Iterator, Optional
import io


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

    def insert_metric_copy(self, metrics: list[str]) -> None:
        with open(self.db_buffer_path, "w+b") as f:
            # Open file for reading and writing in binary mode, truncating its content
            f.truncate(40916)  # See https://stackoverflow.com/a/46883365
            with Text_mmap(f.fileno(), 0) as mmap_buffer:
                for metric_json in metrics:
                    log.info(metric_json)
                    metric = json.loads(metric_json)
                    metric_str = (
                        "|".join(
                            map(
                                str,
                                (
                                    metric["time"],
                                    metric["web_url"],
                                    metric["http_status"],
                                    metric["resp_time"],
                                    metric["regex_match"],
                                ),
                            )
                        )
                        + "\n"
                    )
                    # Indicate to DB that this is the end of data
                    log.debug(f"metric_str: {metric_str}")
                    # Encode metric to bynary (see: https://stackoverflow.com/a/17500651) and write to buffer
                    mmap_buffer.write(metric_str)

                with self.db_connect.cursor() as db_cursor:
                    db_cursor.copy_from(mmap_buffer, self.db_table, sep="|")
