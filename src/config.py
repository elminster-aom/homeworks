# TODO: Use a more secure storage for secrets (e.g. hashicorp vault), actual security is readonly access for .env owner

import dotenv
import logging

log = logging.getLogger("homeworks")


def load_file_into_set(file_path: str) -> set:
    try:
        with open(file_path, "rt") as f:
            result_set = set(map(str.strip, f))
    except IOError:
        log.exception(f"Could not read config file '{file_path}'")
        raise

    return result_set


__dotenv_dict = dotenv.dotenv_values()
db_uri = __dotenv_dict["POSTGRESS_URI"]
db_table = "web_health_metrics"
monitored_url_targets = load_file_into_set(__dotenv_dict["MONITORING_TARGETS_PATH"])
metrics_buffer_path = __dotenv_dict["METRICS_BUFFER_PATH"]
log.debug(
    f"db_uri={db_uri}, db_table={db_table} monitored_url_targets={monitored_url_targets}"
)
