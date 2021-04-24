#!/usr/bin/env python3

# import daemon
import logging
import sys
import src.config as config
from src.get_request_thread import Get_request_thread

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


def waitting_threads_ending_loop(threads: list[Get_request_thread]):
    """Wait for threads to end, however these threads stop only
    when they're killed; therefore process becomes a daemon and
    it runs for always

    Args:
        urls (list[Get_request_thread]): List of threads waiting to end
    """
    for thread in threads:
        thread.join()

    log.warning("All threads stoppped by themselves")


def main() -> int:
    """Main pogram

    Returns:
        int: Return 0 if all went without issue (Note: Ctrl+break is considered normal way to stop it and it should exit 0)
    """
    result = 1
    threads = []
    try:
        for url in config.monitored_url_targets:
            log.debug(f"Creating Thread for URL: {url}")
            thread = Get_request_thread(url)
            thread.start()
            threads.append(thread)

        # TODO: URGENT! Run next call under 'daemon.DaemonContext()' context, following specifications PEP 3143
        waitting_threads_ending_loop(threads)
    except KeyboardInterrupt:
        result = 0
        log.info("Keyboard interruption received (Ctrl+break)")
    except Exception:
        log.exception("Unexpected error")
    else:
        result = 0
    finally:
        return result


if __name__ == "__main__":
    init_logging()
    result = 255
    result = main()

    sys.exit(result)
