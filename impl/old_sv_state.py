#!/usr/bin/python

from __future__ import division, print_function, unicode_literals

import gps
import logging
import sys
import argparse
import math
import stats

from gps.sirf_messages import *

def setup_logging():
    logging.basicConfig(
        format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level = logging.INFO
    )

setup_logging()

logger = logging.getLogger('main')
logger.setLevel(logging.DEBUG)

arg_parser = argparse.ArgumentParser(
    description="Calculate the differences between " +
    "a new position and corrected previous position")
arg_parser.add_argument('gps',
    help="Gps port or recording.")
arg_parser.add_argument('--precision', default=1000, type=int,
    help="Multiplier for fixed point arithmetic.")
arguments = arg_parser.parse_args()

x = gps.open_gps(arguments.gps)

logger.info("Starting.")

last_state = {}
errors = stats.Stats(arguments.precision)

try:
    for msg in x:
        if not isinstance(msg, NavigationLibrarySVStateData):
            continue

        if msg.satellite_id in last_state:
            last = last_state[msg.satellite_id]

            time_diff = msg.gps_time - last.gps_time
            corrected_pos = last.pos + time_diff * last.v

            pos_diff = corrected_pos - msg.pos
            distance = math.sqrt(pos_diff * pos_diff.T)

            #if msg.satellite_id == 32:
            #    print(time_diff, pos_diff, distance)

            if distance < 10:
                print(distance)
                errors.add(distance)
        
        last_state[msg.satellite_id] = msg
except KeyboardInterrupt:
    logger.info("Terminating.")

print("mean error: {}".format(errors.mean()))
print("maximal error: {}".format(errors.maximum))
