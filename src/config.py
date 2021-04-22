# TODO: Use a more secure storage for secrets (e.g. hashicorp vault), actual security is readonly access for .env owner

import dotenv
import logging

log = logging.getLogger("homeworks")


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
        log.debug(
            f"db_uri={self.db_uri}, db_table={self.db_table} monitored_url_targets={self.monitored_url_targets}"
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
