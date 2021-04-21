# TODO: Use a more secure storage for secrets (e.g. hashicorp vault), actual security is readonly access for .env owner

import dotenv


class Config:
    """
    Config class load application's seetings and publishes them for rest of application modules
    """

    def __init__(self):
        dotenv_dict = dotenv.dotenv_values()
        self.db_uri = dotenv_dict["POSTGRESS_URI"]
        self.db_table = "web_health_metrics"
