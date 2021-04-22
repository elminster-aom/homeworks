# TODO: Use a more secure storage for secrets (e.g. hashicorp vault), actual security is readonly access for .env owner

import dotenv
import logging

log = logging.getLogger(__name__)


class Config:
    """
    Config class loads application's seetings and publishes them for rest of application modules
    """

    def __init__(self):
        dotenv_dict = dotenv.dotenv_values()
        self.db_uri = dotenv_dict["POSTGRESS_URI"]
        self.db_table = "web_health_metrics"
        self.monitored_url_targets = self.load_file_into_set(
            dotenv_dict["MONITORING_TARGETS_PATH"]
        )

    @staticmethod
    def load_file_into_set(file_path):
        try:
            with open(file_path, "rt") as f:
                result_set = set(map(str.strip, f))
        except IOError:
            log.exception(f"Could not read config file '{file_path}'")
            raise

        return result_set
