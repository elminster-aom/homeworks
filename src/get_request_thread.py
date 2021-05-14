import datetime
import re
import requests
import threading
import time
from . import config
from . import logging_console
from src.communication_manager import Communication_manager

# See: How to create tzinfo when I have UTC offset? https://stackoverflow.com/a/28270767
from dateutil import tz

log = logging_console.getLogger("homeworks")


class Get_request_thread(threading.Thread):
    def __init__(self, urls: list[str]):
        threading.Thread.__init__(self)
        self.sampling_data = self.initialize_sampling_data(urls)
        self.metrics_sender = Communication_manager()
        if config.monitored_url_regex:
            self.regex_pattern = re.compile(config.monitored_url_regex, re.MULTILINE)
        else:
            self.regex_pattern = None

        self.monitored_url_retry_secs = int(config.monitored_url_retry_secs)
        self.get_request_timeout = 15
        log.debug(f"{self.name}: Instantiated for URLs: {urls}")

    def __delete__(self):
        """Close connection with Kafka when our object instance is destroyed"""
        self.metrics_sender.close_producer()

    @staticmethod
    def initialize_sampling_data(urls: list[str]) -> list[dict]:
        """Initialize sampling data structure with default values

        Args:
            urls (list[str]): List of URLs to monitor by this thread

        Returns:
            list[dict]: Structure with our sampling dta, a list of dictionaries
            where every item is one of the URLs to monitor
        """
        return [
            {
                "time": "",
                "web_url": url,
                "http_status": 0,
                "resp_time": -1,
                "regex_match": None,
            }
            for url in urls
        ]

    @staticmethod
    def get_now_datetime() -> str:
        """Gets NOW date time

        Returns:
            str: Date time in ISO 8601 without 'T' and with TimeZone offset
        """
        now = datetime.datetime.now(tz=tz.tzlocal())
        return now.strftime("%Y-%m-%d %H:%M:%S.%f%z")

    def monitor_one_url(self, sample: dict):
        """By `url_num`, identify which URL ot monitor and collect its revelant info

        Note: requests.get() can raise "During handling of the above exception, another exception occurred"
        for error DNS_PROBE_FINISHED_NXDOMAIN.
        Based on https://stackoverflow.com/a/52725410 and  https://www.python.org/dev/peps/pep-0409/,
        the only solution seems to be supressing context but I discard it because it would
        make difficult to debug other errors, therefore I decided to NOT not apply PEP 409

        Args:
            url_num (int): Index array for `self.sampling_data`
        """
        # fmt: off
        log.debug(f"{self.name}, {sample['web_url']}: Collecting http metrics")
        sample["time"] = self.get_now_datetime()
        get_request = requests.get(sample['web_url'], timeout=self.get_request_timeout)
        sample["http_status"] = get_request.status_code
        sample["resp_time"] = get_request.elapsed.total_seconds()
        if self.regex_pattern:
            if self.regex_pattern.search(get_request.text):
                sample["regex_match"] = True
            else:
                sample["regex_match"] = False
        # fmt: on

    def run(self):
        log.info(f"{self.name}: Starting monitoring")
        while True:
            for sample in self.sampling_data:
                try:
                    self.monitor_one_url(sample)
                except KeyboardInterrupt:
                    log.info(f"{self.name}: ctrl+break")
                    break
                except requests.exceptions.Timeout:
                    log.warning(
                        f"{self.name}, {sample['web_url']}: GET request to timeout after {self.get_request_timeout} seconds"
                    )
                    sample["http_status"] = 504
                    pass
                except requests.exceptions.RequestException:
                    log.exception(
                        f"{self.name}, {sample['web_url']}: Cannot stablish connection"
                    )
                    sample["http_status"] = 503
                    pass

                log.debug(
                    f"{self.name}, {sample['web_url']}: Collected metrics at {sample['time']}"
                )
                self.publish_data(sample)
                log.debug(f"{self.name}, {sample['web_url']}: Published metrics")
            log.debug(
                f"{self.name}: Goes to sleep for {self.monitored_url_retry_secs} seconds now"
            )
            time.sleep(self.monitored_url_retry_secs)

    def publish_data(self, sample: dict):
        self.metrics_sender.produce_message(sample)
