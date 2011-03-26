#!/usr/bin/python3

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
    description="Calculate the UERE from recorded data.\n"
    "Assumes that the receiver was stationary during whole recording.")

arg_parser.add_argument('gps',
    help="Gps port or recording.")
arg_parser.add_argument('--filter', default=None, type=int,
    help="Only print messages with this ID.")
arguments = arg_parser.parse_args()

x = gps.open_gps(arguments.gps)

try:
    for msg in x:
        if arguments.filter is not None and msg.message_id != arguments.filter:
            continue
        print(msg)
        print()
except KeyboardInterrupt:
    logger.info("Terminating.")
