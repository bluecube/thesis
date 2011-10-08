#!/usr/bin/python3

import logging
import numpy
import math
import argparse

import gps

from gps.sirf_messages import *

def setup_logging():
    logging.basicConfig(
        format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level = logging.DEBUG
    )

    gps = logging.getLogger("localization.gps")
    gps.setLevel(logging.INFO)

    replay = logging.getLogger("localization.gps-replay")
    replay.setLevel(logging.INFO)


setup_logging()

logger = logging.getLogger('main')

arg_parser = argparse.ArgumentParser(
    description="Calculate the ECEF position as an "
    "average of positions from msg id 2")
arg_parser.add_argument('gps',
    help="GPS port or recording file.")
arg_parser.add_argument('--precision', default=1000, type=int,
    help="Multiplier for fixed point arithmetic.")

arguments = arg_parser.parse_args()

gps_dev = gps.open_gps(arguments.gps)

logger.info("Starting.")

count = 0
x = 0
y = 0
z = 0

try:
    for msg in gps_dev:
        if isinstance(msg, MeasureNavigationDataOut):
            count += 1
            x += int(arguments.precision * msg.pos[0, 0])
            y += int(arguments.precision * msg.pos[0, 1])
            z += int(arguments.precision * msg.pos[0, 2])
except KeyboardInterrupt:
    logger.info("Ok, that should be enough.")

logger.info("Found " + str(count) + " messages.")

if count != 0:
    receiver_pos = (
        (x / count) / arguments.precision,
        (y / count) / arguments.precision,
        (z / count) / arguments.precision)

    print("{0[0]!r},{0[1]!r},{0[2]!r}".format(receiver_pos))
