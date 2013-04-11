#!/usr/bin/python

from __future__ import division, print_function, unicode_literals

import gps
import gps.message_observer
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
    description="Calculate the differences between two successive linearizations"
    "of SV position.")
arg_parser.add_argument('gps',
    help="Gps port or recording.")
arg_parser.add_argument('--precision', default=1000, type=int,
    help="Multiplier for fixed point arithmetic.")
arguments = arg_parser.parse_args()

x = gps.open_gps(arguments.gps)

logger.info("Starting.")

last_state = {}
errors = stats.Stats(arguments.precision)
interp_distance = stats.Stats(arguments.precision)

@gps.message_observer_decorator(NavigationLibrarySVStateData)
def test(msg):
    if msg.satellite_id in last_state:
        last = last_state[msg.satellite_id]

        time_diff = msg.gps_time - last.gps_time
        corrected_pos = last.pos + time_diff * last.v

        pos_diff = corrected_pos - msg.pos
        distance = math.sqrt(pos_diff * pos_diff.T)

        if distance < 10:
            errors.add(distance)
            interp_distance.add(time_diff)

    last_state[msg.satellite_id] = msg

try:
    x.loop([test])
except KeyboardInterrupt:
    logger.info("Terminating.")

print("mean error: {}".format(errors.mean()))
print("maximal error: {}".format(errors.maximum))
print("mean interpolation distance: {}".format(interp_distance.mean()))
print("maximal interpolation distance: {}".format(interp_distance.maximum))
