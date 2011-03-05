#!/usr/bin/python3

import gps_open
import gps_replay
    # we need to know if this is the replay to keep the timestamps
    # if we're re-recording
import logging
import time
import sys
import gzip
import pickle

def setup_logging():
    logging.basicConfig(
        format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level = logging.INFO
    )

setup_logging()

logger = logging.getLogger('main')
logger.setLevel(logging.DEBUG)

if len(sys.argv) != 3:
    logger.error("Usage: " + sys.argv[0] + " <port> <recording>")
    sys.exit(1)

f = gzip.GzipFile(sys.argv[2], 'wb')

x = gps_open.open_gps(sys.argv[1])

if isinstance(x, gps_replay.GpsReplay):
    pickle.dump(x.start_time, f)
else:
    pickle.dump(time.time(), f)

pickle.dump(x._sirf_version_string, f)

try:
    while True:
        msg = x._read_binary_sirf_msg()
        row = x.last_msg_time, msg
        
        pickle.dump(row, f)
        
except KeyboardInterrupt:
    logger.info("Terminating")
except Exception as e:
    logger.info("Got exception: " + str(e) + ", terminating.")
