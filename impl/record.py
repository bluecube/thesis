#!/usr/bin/python3

import gps
import gps.gps_replay
    # we need to know if this is the replay to keep the timestamps
    # if we're re-recording
import logging
import time
import sys
import gzip
import argparse

def setup_logging():
    logging.basicConfig(
        format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level = logging.INFO
    )

def write_number(f, n):
    f.write(repr(n).encode('ascii'))
    f.write(b'\n')

def write_bytes(f, b):
    write_number(target, len(b))
    f.write(b)

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

target = gzip.open(arguments.target, 'wb')
source = gps.open_gps(arguments.source)

if isinstance(source, gps.gps_replay.GpsReplay):
    write_number(target, source.start_time)
else:
    write_number(target, time.time())

write_bytes(target, source._sirf_version_string.encode('ascii'))

try:
    while True:
        write_bytes(target, source._read_binary_sirf_msg())
        write_number(target, source.last_msg_time)

except KeyboardInterrupt:
    logger.info("Terminating")
except EOFError:
    logger.info("End of recorded data.")
