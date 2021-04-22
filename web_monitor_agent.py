import datetime
import re
import logging
import requests
import sys

# import src.logging_console as logging_console
from src.config import Config

# See: How to create tzinfo when I have UTC offset? https://stackoverflow.com/a/28270767
from dateutil import tz

# TODO: Implement inserts in DB, see: https://hakibenita.com/fast-load-data-python-postgresql
log = logging.getLogger(__name__)


def init_logging():
    """Initialization of basic logging to console, stdout and stderr, where
    log level INFO goes to stdout and everything else goes to stderr
    See: https://stackoverflow.com/a/31459386, How can INFO and DEBUG logging message be sent to stdout and higher level message to stderr?
    """

    class IsEqualFilter(logging.Filter):
        def __init__(self, level, name=""):
            logging.Filter.__init__(self, name)
            self.level = level

        def filter(self, record):
            # non-zero return means we log this message
            return 1 if record.levelno == self.level else 0

    class IsNotEqualFilter(logging.Filter):
        def __init__(self, level, name=""):
            logging.Filter.__init__(self, name)
            self.level = level

        def filter(self, record):
            # non-zero return means we log this message
            return 1 if record.levelno != self.level else 0

    logging_handler_out = logging.StreamHandler(sys.stdout)
    logging_handler_out.addFilter(IsEqualFilter(logging.INFO))
    log.addHandler(logging_handler_out)
    logging_handler_err = logging.StreamHandler(sys.stderr)
    logging_handler_err.addFilter(IsNotEqualFilter(logging.INFO))
    log.addHandler(logging_handler_err)
    # Prevent exception logging while emitting
    logging.raiseExceptions = False


def main():
    """Main pogram"""
    config = Config()
    now = datetime.datetime.now(tz=tz.tzlocal()).strftime("%Y-%m-%d %H:%M:%S.%f%z")

    for url in config.monitored_url_targets:
        pass

    get_request = requests.request("GET", url)
    regex_compiled = re.compile("hola", re.MULTILINE)
    regex_match = regex_compiled.search(get_request.text) != None

    log.info(
        f"""time={now} web_url={url} http_status={get_request.status_code} resp_time={get_request.elapsed.total_seconds()} regex_match={regex_match}"""
    )


if __name__ == "__main__":
    init_logging()
    log.setLevel(logging.INFO)  # set to DEBUG for early-stage debugging

    try:
        main()
    except Exception as e:
        log.exception("Raised exception to main")
