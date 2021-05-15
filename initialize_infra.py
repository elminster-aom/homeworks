#!/usr/bin/env python3
"""Independent module for initializing the environment. It has to be run only once (per environment) before running the main program.
1. It assumes that PostgresSQL is up and running and we have administrative authorization
2. It assumes that Kafka is up and running and we have administrative authorization
3. It enables TimescaleDB extension in PostgresSQL
4. It creates a table for storing web_health monitoring
5. It turns previous table in a partitioned hypertable for storing monitoring metrics
"""

import sys
from homeworks import logging_console
from homeworks.communication_manager import Communication_manager
from homeworks.store_manager import Store_manager

log = logging_console.getLogger("homeworks")


def main() -> int:
    """Main program

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
        return result


if __name__ == "__main__":
    logging_console.init_logging()
    result = 255
    result = main()

    sys.exit(result)
