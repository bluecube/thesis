#!/usr/bin/python

from __future__ import division, print_function, unicode_literals

import gps
import logging
import sys
import argparse

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
    description="Setup mode of the GPS and finish")

arg_parser.add_argument('gps',
    help="Port with a GPS receiver.")
arg_parser.add_argument('--protocol',
    help="To which mode to switch the receiver, protocol is either 'NMEA' or 'SIRF'",
    default="SIRF")
arguments = arg_parser.parse_args()

x = gps.gps.Gps(arguments.gps)
x.set_protocol(arguments.protocol)
