import json
import logging
from . import db_insert

log = logging.getLogger("homeworks")
db = db_insert.Metrics_send(
    db_uri="postgres://avnadmin:wqbzaoclqmojvzue@pg-2e0b09c6-elminster-ef1d.aivencloud.com:21836/defaultdb?sslmode=require",
    db_table="web_health_metrics",
    db_buffer_path="/Users/aleoliva/aiven/homeworks/var/metrics_buffer.txt",
)


class Metrics_send:
    def __init__(self):
        pass

    def send(self, data):
        try:
            json_string = json.dumps(data)
        except json.JSONDecodeError:
            log.exception(f"JSON encoding failed for {data}")
        else:
            log.debug(f"Encoded JSON data: {json_string}")
            db.insert_metric_copy([json_string])

    @staticmethod
    def kafka_producer(data_string):
        pass
