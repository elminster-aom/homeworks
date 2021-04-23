import datetime
import logging
import re
import requests
import threading
import time

# See: How to create tzinfo when I have UTC offset? https://stackoverflow.com/a/28270767
from dateutil import tz

log = logging.getLogger("homeworks")


class Get_request_thread(threading.Thread):
    def __init__(
        self, url, metric_send_object, regex_str="", sampling_frequency_secs=10
    ):
        threading.Thread.__init__(self)
        self.sampling_data = {
            "time": None,
            "web_url": url,
            "http_status": 0,
            "resp_time": -1,
            "regex_match": None,
        }
        self.metric_send_object = metric_send_object
        if regex_str:
            self.regex_pattern = re.compile(regex_str, re.MULTILINE)
        else:
            self.regex_pattern = None

        self.sampling_frequency_secs = sampling_frequency_secs
        self.get_request_timeout = 15
        log.debug(self.sampling_data)

    def run(self):
        while True:
            self.sampling_data["time"] = datetime.datetime.now(
                tz=tz.tzlocal()
            ).strftime("%Y-%m-%d %H:%M:%S.%f%z")
            try:
                get_request = requests.get(
                    self.sampling_data["web_url"], timeout=self.get_request_timeout
                )
                self.sampling_data["http_status"] = get_request.status_code
                self.sampling_data["resp_time"] = get_request.elapsed.total_seconds()

                if self.regex_pattern:
                    if self.regex_pattern.search(get_request.text):
                        self.sampling_data["regex_match"] = True
                    else:
                        self.sampling_data["regex_match"] = False

                self.publish_data()
            except KeyboardInterrupt:
                log.info("ctrl+break")
                break
            except requests.exceptions.Timeout:
                log.warning(
                    f"GET request to {self.sampling_data['web_url']} timeout after {self.sampling_frequency_secs} seconds"
                )
                self.sampling_data["http_status"] = 504
                pass
            except requests.exceptions.RequestException:
                log.exception(
                    f"Cannot stablish connection with {self.sampling_data['web_url']}"
                )
                self.sampling_data["http_status"] = 503
                break

            time.sleep(self.sampling_frequency_secs)

    def publish_data(self):
        self.metric_send_object.send(self.sampling_data)
