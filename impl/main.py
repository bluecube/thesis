#!/usr/bin/python3

import gps
import logging

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

x = gps.Gps('/dev/ttyUSB0')

try:
    for msg in x.messages():
        logger.info("Message: " + str(msg))
except KeyboardInterrupt:
    logger.info("Terminating")
