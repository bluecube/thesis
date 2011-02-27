#!/usr/bin/python3

import logging
import sys
import numpy
import math

import gps_replay

from sirf_messages import *

C = 299792458

# plot "/tmp/clock_offset.plot" using 1:2 with lines linestyle 1 title "clock offset" "/tmp/clock_offset.plot" using 1:3 with lines linestyle 2 title "derivation of clock offset"

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    gps = logging.getLogger("localization.gps")
    gps.setLevel(logging.INFO)

    replay = logging.getLogger("localization.gps-replay")
    replay.setLevel(logging.INFO)

def estimate_position():
    logger.info("Pass 1: Estimate receiver position.")

    gps = gps_replay.GpsReplay(sys.argv[1])

    count = 0
    receiver_pos = numpy.matrix([[0., 0., 0.]])
    try:
        while True:
            msg = gps.read_specific_message(MeasureNavigationDataOut)
            
            count += 1
            receiver_pos += msg.pos
    except KeyboardInterrupt:
        logger.info("Terminating.")
        exit(0)
    except EOFError:
        pass

    receiver_pos /= count
    logger.debug("Found " + str(count) + " messages, average position is " + str(receiver_pos) + ".")

    return receiver_pos

def analyze_clock_offsets(receiver_pos):
    logger.info("Pass 2: Analyze clock offsets.")

    gps = gps_replay.GpsReplay(sys.argv[1])

    last_time = None
    sv = {}
    measurements = []

    plot = open(sys.argv[2], 'wt')

    try:
        while True:
            msg = gps.read_message()

            if isinstance(msg, NavigationLibraryMeasurementData):
                if last_time == msg.gps_sw_time:
                    measurements.append(msg)
                else:
                    new_clock_offset = process_clock_offsets_batch(measurements, sv, receiver_pos)
                    if not (last_time is None or clock_offset is None):
                        clock_drift = (new_clock_offset - clock_offset) / (msg.gps_sw_time - last_time)

                        print(last_time, new_clock_offset, clock_drift, file=plot)

                    measurements = [msg]
                    last_time = msg.gps_sw_time
                    clock_offset = new_clock_offset
                    
            elif isinstance(msg, NavigationLibrarySVStateData):
                sv[msg.satellite_id] = msg

    except KeyboardInterrupt:
        logger.info("Terminating.")
        exit(0)
    except EOFError:
        pass

def process_clock_offsets_batch(measurements, sv, pos):
    offset_sum = 0
    offset_count = 0

    if len(measurements) == 0:
        return

    for data in measurements:
        if data.pseudorange == 0:
            print("Pseudorange == 0")
            continue

        sv_data = sv[data.satellite_id]
        time_of_transmission = data.gps_sw_time - data.pseudorange / C

        sv_pos = sv_data.pos
        sv_pos += (sv_data.gps_time - time_of_transmission) * sv_data.v

        distance = sv_pos - pos

        geom_range = math.sqrt(distance * distance.T)

        clock_offset = (data.pseudorange - sv_data.iono_delay - geom_range) / C

        print("Satellite is at " + str(sv_pos) + "; pseudorange = " +
            str(data.pseudorange) + "; range = " + str(geom_range) +
            "; clock offset = " + str(clock_offset))
        
        offset_count += 1
        offset_sum += clock_offset

    clock_offset = offset_sum / offset_count

    print("Average clock offset is " + str(clock_offset))

    return clock_offset

setup_logging()

logger = logging.getLogger('main')
logger.setLevel(logging.DEBUG)

logger.info("Calculate the UERE from recorded data.")
logger.info("Assumes that the receiver was stationary during whole recording.")

if len(sys.argv) != 3:
    logger.error("Usage: " + sys.argv[0] + " <recording> <plot file>")
    sys.exit(1)

pos = estimate_position()
analyze_clock_offsets(pos)

