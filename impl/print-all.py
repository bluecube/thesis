#!/usr/bin/python
"""
print-all.py

Print all messages from the gps."""

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

arg_parser = argparse.ArgumentParser(description="Print all messages from the gps.")

arg_parser.add_argument('gps',
    help="Gps port or recording.")
arg_parser.add_argument('--filter', default=None, type=int,
    help="Only print messages with this ID.")
arg_parser.add_argument('--no-separators', default=False, action='store_true',
    help="Disable the display of separators in long pauses?")
arguments = arg_parser.parse_args()

x = gps.open_gps(arguments.gps)

last_time = float("nan")

count = 0

try:
    while True:
        try:
            msg = x.try_read_message()
        except gps.sirf.UnrecognizedMessageException as e:
            msg = e
        except StopIteration:
            break

        if arguments.filter is not None and msg.message_id != arguments.filter:
            continue

        if x.last_msg_time - last_time > 0.3 and not arguments.no_separators:
            print("***")
            print()
        last_time = x.last_msg_time

        print(msg)
        print()
        count += 1
except KeyboardInterrupt:
    logger.info("Terminating.")

logger.info("Printed %i messages", count)
