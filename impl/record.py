#!/usr/bin/python

import gps.gps_saver
import logging
import sys
import argparse

import gps

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

arg_parser.add_argument('sources', nargs='+',
    help="Source GPS or one or more recordings.")
arg_parser.add_argument('--output',
    help="Target recording.")
arg_parser.add_argument('--verbose', action = 'store_true',
    help="Print status of the GPS roughly every 10 seconds.")
arguments = arg_parser.parse_args()

saver = gps.gps_saver.GpsSaver(arguments.output)

try:
    for source_file in arguments.sources:
        source = gps.open_gps(source_file)
        saver.init_source(source)
        try:
            if arguments.verbose:
                geodetic_nav_data_id = gps.sirf_messages.GeodeticNavigationData.get_message_id()
                counter = 0
                while True:
                    msg = saver.save_message();

                    if gps.sirf.bytes_to_message_id(msg) == geodetic_nav_data_id:
                        counter += 1
                        if counter == 10:
                            msg = gps.sirf.from_bytes(msg)
                            print(msg.status_line())
                            counter = 0

            else:
                saver.save_all();
        except StopIteration:
            break
except KeyboardInterrupt:
    logger.info("Terminating")
