"""All parametrization for our monintoring tool is centralized here
"""
# TODO: Use a more secure storage for secrets (e.g. hashicorp vault), currently security is implemented as read-only access for file-owner on .env
# TODO: Encrypt password after using them (accessing them with a method) so that they have less chance to appear clear-text, e.g. with system dump

import dotenv
from . import logging_console


def load_file_into_list(file_path: str) -> list[str]:
    """It reads the URLs of our monitoring targets (Webs to monitor)
    from a config file and returns them as a `list` object.

    Args:
        file_path (str): Full path to config file with the URLs

    Returns:
        list[str]: URLs loaded from config file
    """
    try:
        with open(file_path, "rt") as f:
            lines = [line.rstrip() for line in f]
    except IOError:
        raise IOError(f"Could not read config file '{file_path}'")
    return lines


_dotenv_dict = dotenv.dotenv_values()

db_autocommit = _dotenv_dict["POSTGRES_AUTOCOMMIT"]
db_uri = _dotenv_dict["POSTGRES_URI"]
db_table = _dotenv_dict["POSTGRES_TABLE"]
kafka_access_cert = _dotenv_dict["KAFKA_ACCESS_CERTIFICATE"]
kafka_access_key = _dotenv_dict["KAFKA_ACCESS_KEY"]
kafka_ca_cert = _dotenv_dict["KAFKA_CA_CERTIFICATE"]
kafka_uri = _dotenv_dict["KAFKA_SERVICE_URI"]
kafka_topic_name = _dotenv_dict["KAFKA_TOPIC_NAME"]
monitored_log_level = _dotenv_dict["MONITORING_LOG_LEVEL"]
monitored_url_targets = load_file_into_list(_dotenv_dict["MONITORING_TARGETS_PATH"])
monitored_url_regex = _dotenv_dict["MONITORING_TARGETS_REGEX"]
monitored_url_retry_secs = _dotenv_dict["MONITORING_RETRY_SECS"]

# Delete temporary variable, it was only needed for initialization
del _dotenv_dict
