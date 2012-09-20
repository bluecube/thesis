#!/usr/bin/python

import gps.gps_saver
import logging
import sys
import argparse

import gps.sirf

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
arg_parser.add_argument('--verbose', action = 'store_true',
    help="Print status of the GPS roughly every 10 seconds.")
arguments = arg_parser.parse_args()

saver = gps.gps_saver.GpsSaver(arguments.source, arguments.target)

try:
    try:
        if arguments.verbose:
            geodetic_nav_data_id = gps.sirf_messages.GeodeticNavigationData.get_message_id()
            counter = 0
            while True:
                msg = saver.save_message();

                # TODO: Refactor this somewhere more up the stream
                if gps.sirf.bytes_to_message_id(msg) == geodetic_nav_data_id:
                    counter += 1
                    if counter == 10:
                        msg = gps.sirf.from_bytes(msg)
                        print(msg.status_line())
                        counter = 0

        else:
            saver.save_all();
    except StopIteration:
        pass
except KeyboardInterrupt:
    logger.info("Terminating")
