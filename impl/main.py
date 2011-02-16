#!/usr/bin/python3

import gps_wrapper
import logging
import sys

from sirf_messages import *

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

setup_logging()

logger = logging.getLogger('main')
logger.setLevel(logging.DEBUG)

if len(sys.argv) != 2:
    logger.error("Usage: " + sys.argv[0] + " <port or recording>")
    sys.exit(1)

x = gps_wrapper.GpsWrapper(sys.argv[1])

try:
    for msg in x.messages():
        logger.info("Message: " + str(msg))
except KeyboardInterrupt:
    logger.info("Terminating.")
except EOFError:
    logger.info("End of recording.")
