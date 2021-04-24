#!/usr/bin/env python3

# import daemon
import logging
import sys
from src.communication_manager import Communication_manager
from src.store_manager import Store_manager

log = logging.getLogger("homeworks")
log.setLevel(logging.DEBUG)  # set to DEBUG for early-stage debugging


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


def sink_data():
    """While connection to communication bus is still stablished, batchs of messages
    are retrieved and store in DB
    * Loop can be interrupted witha Ctr+Break
    """
    metrics_retriever = Communication_manager()
    metrics_inserter = Store_manager()
    while True:
        try:
            messages = metrics_retriever.consume_messages()
            metrics_inserter.insert_metric_copy(messages)
        except KeyboardInterrupt:
            log.info("Keyboard interruption received (Ctrl+break)")
            break
        except Exception:
            log.exception("Unexpected error")
            raise


def main() -> int:
    """Main pogram

    Returns:
        int: Return 0 if all went without issue (Note: Ctrl+break is considered normal way to stop it and it should exit 0)
    """
    result = 0
    try:
        # TODO: URGENT! Run next call under 'daemon.DaemonContext()' context, following specifications PEP 3143
        sink_data()
    except Exception:
        result = 1
        log.exception("Unexpected error")
    finally:
        return result


if __name__ == "__main__":
    init_logging()
    result = 255
    result = main()

    sys.exit(result)
