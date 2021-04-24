"""All paremetrization for our monintoring tool is centrazlized here
"""
# TODO: Use a more secure storage for secrets (e.g. hashicorp vault), actual security is readonly access for .env owner
# TODO: Encrypt password after using them (accessingt them with a method), therefore they have less chance toappear clear-text, e.g. with system dump

import dotenv
import logging

log = logging.getLogger("homeworks")


def load_file_into_set(file_path: str) -> set:
    """It reads the URLs of our monitoring targets (Webs to monitor)
    from a config file and returns them as a `set` object, therefore
    duplicate URLs are skipped

    Args:
        file_path (str): Full path to config file with the URLs

    Returns:
        set: URLs loaded from config file
    """
    try:
        with open(file_path, "rt") as f:
            result_set = set(map(str.strip, f))
    except IOError:
        log.exception(f"Could not read config file '{file_path}'")
        raise

    return result_set


_dotenv_dict = dotenv.dotenv_values()

db_autocommit = _dotenv_dict["POSTGRES_AUTOCOMMIT"]
db_uri = _dotenv_dict["POSTGRES_URI"]
db_table = _dotenv_dict["POSTGRES_TABLE"]
kafka_access_cert = _dotenv_dict["KAFKA_ACCESS_CERTIFICATE"]
kafka_access_key = _dotenv_dict["KAFKA_ACCESS_KEY"]
kafka_ca_cert = _dotenv_dict["KAFKA_CA_CERTIFICATE"]
kafka_uri = _dotenv_dict["KAFKA_SERVICE_URI"]
kafka_topic_name = _dotenv_dict["KAFKA_TOPIC_NAME"]
monitored_url_targets = load_file_into_set(_dotenv_dict["MONITORING_TARGETS_PATH"])
monitored_url_regex = _dotenv_dict["MONITORING_TARGETS_REGEX"]
monitored_url_retry_secs = _dotenv_dict["MONITORING_RETRY_SECS"]

# Delete temporal varialbe, it was only needed for initialization
del _dotenv_dict

log.debug(
    f"db_uri={db_uri}, db_table={db_table} monitored_url_targets={monitored_url_targets}"
)
