#!/usr/bin/env python3

"""Retrieves (Consumer) metrics from a Kafka topic and stores it in a PostgresSQL hypertable
"""

# import daemon
import sys
from homeworks import logging_console
from homeworks.communication_manager import Communication_manager
from homeworks.store_manager import Store_manager

log = logging_console.getLogger("homeworks")


def sink_data(metrics_retriever: None, metrics_inserter: None):
    """While connection to the communication bus is still established, batches of messages
    are retrieved and stored in the DB
    Loop can be interrupted with a Ctr+Break

    Args:
        metrics_retriever (Communication_manager): Manages Kafka communication

        metrics_inserter (Store_manager): Manages PostgresSQL storage
    """
    while True:
        try:
            messages = metrics_retriever.consume_messages()
            metrics_inserter.insert_metrics_batch(messages)
        except KeyboardInterrupt:
            log.info("Keyboard interruption received (Ctrl+break)")
            break
        except Exception:
            log.exception("Unexpected error")
            raise


def main() -> int:
    """Main program

    Returns:
        int: Return 0 if all ran without issues (Note: Ctrl+break is considered a normal way to stop it and it should exit with 0)
    """
    result = 0
    retriever = None
    inserter = None
    try:
        # TODO: URGENT! Run next call under 'daemon.DaemonContext()' context, following specifications PEP 3143
        retriever = Communication_manager()
        inserter = Store_manager()
        sink_data(retriever, inserter)
    except Exception:
        result = 1
        log.exception("Unexpected error")
    finally:
        if retriever:
            retriever.close_consumer()
        if inserter:
            inserter.close()
        return result


if __name__ == "__main__":
    logging_console.init_logging()
    result = 255
    result = main()

    sys.exit(result)
