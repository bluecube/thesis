#!/usr/bin/python3

import logging
import sys
import numpy
import math

import gps_replay

from sirf_messages import *

C = 299792458
    # Speed of light

MAX_CLOCK_DRIFT = 1e-2
    # This is a maximum clock drift (in absolute value) between two
    # measurement groups before we call it a clock correction

class Measurement:
    """
    A single measurement of the user to sv distance, speed, ....
    """
    def __init__(self, msg):
        self.gps_sw_time = msg.gps_sw_time
        self.pseudorange = msg.pseudorange
        self.time = msg.gps_sw_time

        self.satellite_id = msg.satellite_id

    def process_sv(self, svs):
        """
        Because SV data come after the measurement data, we have to
        add this part after the measurement is initialized.
        Returns false if the measurement was valid.
        """

        if self.satellite_id not in svs:
            return False

        if self.pseudorange == 0.0:
            return False

        sv = svs[self.satellite_id]

        time_of_transmission = self.gps_sw_time - self.pseudorange / C

        self.sv_pos = sv.pos + (sv.gps_time - time_of_transmission) * sv.v

        self.iono_delay = sv.iono_delay
        
        return True

    def clock_offset(self, receiver_pos):
        return (self.pseudorange - self.iono_delay -
            self.geom_range(receiver_pos)) / C
        
    def geom_range(self, receiver_pos):
        distance = self.sv_pos - receiver_pos
        return math.sqrt(distance * distance.T)
        

def setup_logging():
    logging.basicConfig(
        format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level = logging.DEBUG
    )

    gps = logging.getLogger("localization.gps")
    gps.setLevel(logging.INFO)

    replay = logging.getLogger("localization.gps-replay")
    replay.setLevel(logging.INFO)

def measurement_generator():
    """
    Yields measurements which are used in passes 2 and 3.
    """

    gps = gps_replay.GpsReplay(sys.argv[1])
    sv = {}

    group = []
    groupTime = None

    for msg in gps:
        if isinstance(msg, NavigationLibraryMeasurementData):
            measurement = Measurement(msg)

            if groupTime == measurement.time:
                group.append(measurement)
            else:
                for x in group:
                    if x.process_sv(sv):
                        yield x

                group = [measurement]
                groupTime = measurement.time
        elif isinstance(msg, NavigationLibrarySVStateData):
            sv[msg.satellite_id] = msg

        for x in group:
            if x.process_sv(sv):
                yield x

def pass_one():
    logger.info("Pass 1: Estimate receiver position.")

    gps = gps_replay.GpsReplay(sys.argv[1])

    count = 0
    receiver_pos = numpy.matrix([[0., 0., 0.]])

    for msg in gps:
        if isinstance(msg, MeasureNavigationDataOut):
            count += 1
            receiver_pos += msg.pos

    receiver_pos /= count
    logger.debug("Found " + str(count) + " messages, average position is " + str(receiver_pos) + ".")

    return receiver_pos

def get_drift(m1, m2, receiver_pos):
    """
    Calculate clock drift between two measurement groups.
    """
    if m1.time == m2.time:
        return 0

    drift = m2.clock_offset(receiver_pos) - m1.clock_offset(receiver_pos)
    drift /= m2.time - m1.time

    return drift

def is_clock_correction(m1, m2, receiver_pos):
    """
    Returns true if there was a clock correction between the 
    two measurements.
    """
    return abs(get_drift(m1, m2, receiver_pos)) > MAX_CLOCK_DRIFT

def pass_two(receiver_pos):
    """
    Splits the measurements into blocks between clock corrections,
    calculates the least squares on the blocks and calls pass
    three on every block.
    """
    logger.info("Pass 2: Analyze clock offsets.")

    generator = measurement_generator()

    block = []

    # the following variables are temporary storage for the least squares.
    # see the notes for better description
    p = 0
    q = 0
    r = 0
    s = 0

    for measurement in generator:
        if len(block) > 0 and is_clock_correction(measurement, block[-1], receiver_pos):
            pass_three(block, receiver_pos, p, q, r, s)

            # reset it all.
            block = []
            p = 0
            q = 0
            r = 0
            s = 0

        block.append(measurement)

        offset = measurement.clock_offset(receiver_pos)
        time = measurement.time - offset

        p += offset * time
        q += offset
        r += time
        s += time * time

    
    pass_three(block, receiver_pos, p, q, r, s)

def pass_three(block, receiver_pos, p, q, r, s):
    """
    Do the main error calculations.
    At this place we know both the physical position of the receiver
    and the (hopefully precise) clock offset.
    """
    # finish the least squares calculation:
    div = 1 / (len(block) * s - r * r)
    a = (len(block) * p - q * r) * div
    b = (q * s - p * r) * div

    print("Found a block:")
    print("  length:", len(block))
    print("  a:     ", a)
    print("  b:     ", b)
    print("  start: ", block[0].time)
    print("  end:   ", block[-1].time)

#    for measurement in block:
#        corrected_pseudorange = measurement.pseudorange - measurement.iono_delay
#        clock_offset = a * measurement.

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

logger.info("Calculate the UERE from recorded data.")
logger.info("Assumes that the receiver was stationary during whole recording.")

if len(sys.argv) != 2:
    logger.error("Usage: " + sys.argv[0] + " <recording>")
    sys.exit(1)

try:
    pos = pass_one()
    pass_two(pos)
except KeyboardInterrupt:
    logger.info("Terminating.")
    exit(0)
