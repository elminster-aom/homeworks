import logging
import sys
from . import config


def getLogger(name=None) -> logging.Logger:
    return logging.getLogger(name)


log = getLogger("homeworks")


def get_log_level() -> int:
    """Convert configuration string in valid logging level value

    Returns:
        int: logging level value
    """
    if config.monitored_log_level == "DEBUG":
        result = logging.DEBUG
    elif config.monitored_log_level == "INFO":
        result = logging.INFO
    elif config.monitored_log_level == "WARNING":
        result = logging.WARNING
    elif config.monitored_log_level == "ERROR":
        result = logging.ERROR
    elif config.monitored_log_level == "FATAL":
        result = logging.FATAL
    else:
        result = None
    return result


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

    log.setLevel(get_log_level())
