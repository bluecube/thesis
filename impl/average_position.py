#!/usr/bin/python

import logging
import numpy
import math
import argparse

import gps

import stats

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
    description="Calculate the average ECEF and WGS84 positions as reported"
    "by the receiver's software.")
arg_parser.add_argument('gps',
    help="GPS port or recording file.")

arguments = arg_parser.parse_args()

gps_dev = gps.open_gps(arguments.gps)

logger.info("Starting.")

count = 0
x = stats.Stats(1000)
y = stats.Stats(1000)
z = stats.Stats(1000)

geod_count = 0
lat = stats.Stats(1000)
lon = stats.Stats(1000)

try:
    for msg in gps_dev:
        if isinstance(msg, MeasureNavigationDataOut):
            count += 1
            x.add(msg.pos[0, 0])
            y.add(msg.pos[0, 1])
            z.add(msg.pos[0, 2])
        elif isinstance(msg, GeodeticNavigationData):
            geod_count += 1
            lat.add(msg.latitude)
            lon.add(msg.longitude)

except KeyboardInterrupt:
    logger.info("Ok, that should be enough.")

logger.info("Found " + str(count) + " MeasureNavigationDataOut messages.")

if count != 0:
    receiver_pos = (x.mean(), y.mean(), z.mean())

    print("{0[0]!r},{0[1]!r},{0[2]!r}".format(receiver_pos))

logger.info("Found " + str(geod_count) + " GeodeticNavigationData messages.")

if geod_count != 0:
    print("latitude: {0!r} longitude: {1!r}".format(lat.mean(), lon.mean()))
