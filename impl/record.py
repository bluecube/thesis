#!/usr/bin/python3

import gps
import logging
import time
import sys
import gzip
import pickle

def setup_logging():
    logging.basicConfig(
        format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level = logging.DEBUG
    )

setup_logging()

logger = logging.getLogger('main')
logger.setLevel(logging.DEBUG)

if len(sys.argv) != 3:
    logger.error("Usage: " + sys.argv[0] + " <port> <recording>")
    sys.exit(1)

f = gzip.GzipFile(sys.argv[2], 'wb')

x = gps.Gps(sys.argv[1])

pickle.dump(time.time(), f)
pickle.dump(x._sirf_version_string, f)

try:
    while True:
        msg = x._read_binary_sirf_msg()
        row = time.time(), msg
        
        pickle.dump(row, f)
        
except KeyboardInterrupt:
    logger.info("Terminating")
