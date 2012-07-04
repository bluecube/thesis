#!/usr/bin/python

import gps.gps_saver
import logging
import sys
import argparse

def setup_logging():
    logging.basicConfig(
        format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level = logging.INFO
    )

setup_logging()

logger = logging.getLogger('main')
logger.setLevel(logging.DEBUG)

arg_parser = argparse.ArgumentParser(
    description="(Re)Record a GPS data stream to a new format.")

arg_parser.add_argument('source',
    help="Source GPS or recording.")
arg_parser.add_argument('target',
    help="Target recording.")
arguments = arg_parser.parse_args()

saver = gps.gps_saver.GpsSaver(arguments.source, arguments.target)

try:
    saver.save_all()
except KeyboardInterrupt:
    logger.info("Terminating")
