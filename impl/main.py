#!/usr/bin/python3

import gps_open
import logging
import sys

from sirf_messages import *

def setup_logging():
    logging.basicConfig(
        format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level = logging.DEBUG
    )

setup_logging()

logger = logging.getLogger('main')
logger.setLevel(logging.DEBUG)

if len(sys.argv) != 2:
    logger.error("Usage: " + sys.argv[0] + " <port or recording>")
    sys.exit(1)

x = gps_open.open_gps(sys.argv[1])

try:
    for msg in x:
        logger.info("Message: " + str(msg))
except KeyboardInterrupt:
    logger.info("Terminating.")
