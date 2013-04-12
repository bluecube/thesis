#!/usr/bin/python
"""
checksum.py

Calculate crc32 checksum from recorded messages' payloads.
Used for verifying integrity of modified recordings.
"""

import gps
import logging
import sys
import argparse
from zlib import crc32

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
    description="Calculate crc32 checksum from recorded messages' payloads.")

arg_parser.add_argument('gps',
    help="Gps port or recording.")
arguments = arg_parser.parse_args()

x = gps.open_gps(arguments.gps)

checksum = crc32(b'')

try:
    while True:
        checksum = crc32(x._read_binary_sirf_msg(), checksum)
except StopIteration:
    pass

print("checksum: {:#08x}".format(checksum & 0xffffffff))
