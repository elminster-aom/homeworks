# import daemon
import logging
import sys

from src.config import Config
from src.get_request_thread import Get_request_thread

# TODO: Implement inserts in DB, see: https://hakibenita.com/fast-load-data-python-postgresql
# TODO: Implement as a daemon, e.g. daemon.DaemonContext()
log = logging.getLogger("homeworks")
log.setLevel(logging.INFO)  # set to DEBUG for early-stage debugging


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


def threads_manager(urls):
    threads = []
    for url in urls:
        thread = Get_request_thread(url)
        # thread.daemon = True
        thread.start()

    for thread in threads:
        thread.join()


def main():
    """Main pogram"""
    config = Config()

    for url in config.monitored_url_targets:
        pass
    # with daemon.DaemonContext():
    try:
        threads_manager(config.monitored_url_targets)
    except KeyboardInterrupt:
        log.info("ctrl+break")


if __name__ == "__main__":
    init_logging()
    try:
        main()
    except Exception as e:
        log.exception("Raised exception to main")
