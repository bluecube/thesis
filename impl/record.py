#!/usr/bin/python3

import gps
import gps.gps_replay
    # we need to know if this is the replay to keep the timestamps
    # if we're re-recording
import logging
import time
import sys
import gzip
import pickle
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
    description="(Re)Record a GPS data stream.")

arg_parser.add_argument('source',
    help="Source GPS or recording.")
arg_parser.add_argument('target',
    help="Target recording.")
arg_parser.add_argument('--pickle-protocol', default=-1, type=int,
    help="Pickle protocol version to use in the recording."
    "Default is to use highest available.")
arguments = arg_parser.parse_args()

target = pickle.Pickler(
    gzip.GzipFile(arguments.target, 'wb'),
    protocol = arguments.pickle_protocol)

source = gps.open_gps(arguments.source)

if isinstance(source, gps.gps_replay.GpsReplay):
    target.dump(source.start_time)
else:
    target.dump(time.time())

target.dump(source._sirf_version_string)

try:
    while True:
        try:
            msg = source._read_binary_sirf_msg()
        except EOFError:
            break

        row = source.last_msg_time, msg
        
        target.dump(row)

except KeyboardInterrupt:
    logger.info("Terminating")
except Exception as e:
    logger.info("Got exception: " + str(e) + ", terminating.")
