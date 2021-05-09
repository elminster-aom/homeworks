#!/usr/bin/env python3
"""Independent module for initializing the environment. It has to be run only once (per environment) before running the main program.
1. It assumes that PosgresSQL is up and running and we have administratitve authorization
2. It assumes that Kafka is up and running and we have administratitve authorization
3. It enables TimescaleDB extension in PostgresSQL
4. It creates a table for storing web_health monitoring
5. It turns previous table in a partitioned hypertable for storing monitoring metrics
"""

import logging
import sys
from src.store_manager import Store_manager
from src.communication_manager import Communication_manager

log = logging.getLogger("homeworks")
log.setLevel(logging.INFO)  # set to DEBUG for early-stage debugging


def init_logging():
    """Initialization of basic logging to console, stdout and stderr, where
    log level INFO goes to stdout and everything else to stderr
    See: https://stackoverflow.com/questions/2302315/how-can-info-and-debug-logging-message-be-sent-to-stdout-and-higher-level-messag
    """
    # TODO: Move this function to an independent module

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


def main() -> int:
    """Main pogram

    Returns:
        int: Return 0 if all setup ran without problems
    """
    result = 0

    # Initialize and validate DB
    store_manager = None
    try:
        store_manager = Store_manager()
        store_manager.initialize_metrics_store()
        is_db_ok = store_manager.validate_metric_store()
    # except is not needed, if any it can be raised, see: https://www.reddit.com/r/learnpython/comments/45erlq/is_it_okay_to_use_tryfinally_without_except/czxk5bk?utm_source=share&utm_medium=web2x&context=3
    finally:
        if store_manager:
            store_manager.close()
    if not is_db_ok:
        result += 1

    # Initialize and validate communication bus
    communication_manager = None
    try:
        communication_manager = Communication_manager()
        is_bus_ok = communication_manager.validate_metrics_communication()
        if not is_bus_ok:
            communication_manager.initialize_metrics_communication()
    except Exception:
        result += 1
        raise
    finally:
        if communication_manager:
            communication_manager.close()
        return result


if __name__ == "__main__":
    init_logging()
    result = 255
    result = main()

    sys.exit(result)
