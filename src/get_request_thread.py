import datetime
import logging
import re
import requests
import threading
import time
from . import config
from src.communication_manager import Communication_manager

# See: How to create tzinfo when I have UTC offset? https://stackoverflow.com/a/28270767
from dateutil import tz

log = logging.getLogger("homeworks")


class Get_request_thread(threading.Thread):
    def __init__(self, url: str):
        threading.Thread.__init__(self)
        self.sampling_data_dict = {
            "time": "",
            "web_url": url,
            "http_status": 0,
            "resp_time": -1,
            "regex_match": None,
        }
        self.metrics_sender = Communication_manager()
        if config.monitored_url_regex:
            self.regex_pattern = re.compile(config.monitored_url_regex, re.MULTILINE)
        else:
            self.regex_pattern = None

        self.monitored_url_retry_secs = config.monitored_url_retry_secs
        self.get_request_timeout = 15
        log.debug(
            f"{self.name}: Instantiated for URL: {self.sampling_data_dict['web_url']}"
        )

    def run(self):
        log.info(f"{self.name}: Starting monitoring")
        while True:
            self.sampling_data_dict["time"] = datetime.datetime.now(
                tz=tz.tzlocal()
            ).strftime("%Y-%m-%d %H:%M:%S.%f%z")
            try:
                get_request = requests.get(
                    self.sampling_data_dict["web_url"], timeout=self.get_request_timeout
                )
                self.sampling_data_dict["http_status"] = get_request.status_code
                self.sampling_data_dict[
                    "resp_time"
                ] = get_request.elapsed.total_seconds()

                if self.regex_pattern:
                    if self.regex_pattern.search(get_request.text):
                        self.sampling_data_dict["regex_match"] = True
                    else:
                        self.sampling_data_dict["regex_match"] = False

            except KeyboardInterrupt:
                log.info("ctrl+break")
                break
            except requests.exceptions.Timeout:
                log.warning(
                    f"GET request to {self.sampling_data_dict['web_url']} timeout after {self.monitored_url_retry_secs} seconds"
                )
                self.sampling_data_dict["http_status"] = 504
                pass
            except requests.exceptions.RequestException:
                log.exception(
                    f"Cannot stablish connection with {self.sampling_data_dict['web_url']}"
                )
                self.sampling_data_dict["http_status"] = 503
                break
            else:
                log.debug(
                    f"{self.name}: Collected metrics at {self.sampling_data_dict['time']}"
                )
                self.publish_data()
                log.debug(f"{self.name}: Published metrics. It goes to sleep now")
            time.sleep(self.monitored_url_retry_secs)

    def publish_data(self):
        self.metrics_sender.produce_message(self.sampling_data_dict)
