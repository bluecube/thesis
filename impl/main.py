#!/usr/bin/python3

import gps
import logging

from sirf_messages import *

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

setup_logging()

x = gps.Gps('/dev/ttyUSB0')

x.send_message(PollSoftwareVersion())

for i in range(5):
    msg = x.read_message()
    print(msg)
