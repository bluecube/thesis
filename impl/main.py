#!/usr/bin/python3

import gps
import logging

import sirf

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

for i in range(30):
    msg = x.get_one()
    print(msg)
