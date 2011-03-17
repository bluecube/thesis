#!/usr/bin/python3

import logging
import sys
import numpy
import math
import argparse
import collections

import gps.gps_replay

from gps.sirf_messages import *

C = 299792458
    # Speed of light

MAX_CLOCK_DRIFT = 1e-2
    # This is a maximum clock drift (in absolute value) between two
    # measurement groups before we call it a clock correction

HISTOGRAM_RESOLUTION = 10
    # Width of error histogram bin in meters.

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
        Returns false if the measurement was invalid.
        """

        if self.satellite_id not in svs:
            return False

        if self.pseudorange == 0.0:
            return False

        sv = svs[self.satellite_id]

        time_of_transmission = self.gps_sw_time - self.pseudorange / C

        self.sv_pos = sv.pos - (sv.gps_time - time_of_transmission) * sv.v

        
        ############################
        self.delays = sv.iono_delay

        distance = self.sv_pos - receiver_pos
        self.geom_range = math.sqrt(distance * distance.T)
        
        self.clock_offset = (self.pseudorange - self.delays - self.geom_range) / C

        return True


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

    replay = gps.gps_replay.GpsReplay(arguments.recording)
    sv = {}

    group = []
    groupTime = None

    for msg in replay:
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

    replay = gps.gps_replay.GpsReplay(arguments.recording)

    count = 0
    receiver_pos = numpy.matrix([[0., 0., 0.]])

    try:
        for msg in replay:
            if isinstance(msg, MeasureNavigationDataOut):
                count += 1
                receiver_pos += msg.pos
    except KeyboardInterrupt:
        logger.info("Ok, that should be enough.")

    receiver_pos /= count
    logger.debug("Found " + str(count) + " messages, average position is " + str(receiver_pos) + ".")

    return receiver_pos

def get_drift(m1, m2):
    """
    Calculate clock drift between two measurement groups.
    """
    if m1.time == m2.time:
        return 0

    drift = m2.clock_offset - m1.clock_offset
    drift /= m2.time - m1.time

    return drift

def is_clock_correction(m1, m2):
    """
    Returns true if there was a clock correction between the 
    two measurements.
    """
    return abs(get_drift(m1, m2)) > MAX_CLOCK_DRIFT

def pass_two():
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

    if not (arguments.group is None):
        last = generator.__next__()

        for i in range(arguments.group):
            for measurement in generator:
                if is_clock_correction(last, measurement):
                    last = measurement
                    block = [measurement]
                    break
                else:
                    last = measurement

        block = [last]
    else:
        block = [generator.__next__()]


    for measurement in generator:
        offset = block[-1].clock_offset
        time = block[-1].time - offset
        p += offset * time
        q += offset
        r += time
        s += time * time

        if is_clock_correction(block[-1], measurement):
            pass_three(block, p, q, r, s)

            if not (arguments.group is None):
                return

            # reset it all.
            block = []
            p = 0
            q = 0
            r = 0
            s = 0

        block.append(measurement)

    offset = block[-1].clock_offset
    time = block[-1].time - offset
    p += offset * time
    q += offset
    r += time
    s += time * time

    pass_three(block, p, q, r, s)

def pass_three(block, p, q, r, s):
    """
    Do the main error calculations.
    At this place we know both the physical position of the receiver
    and the (hopefully precise) clock offset.
    """
    # finish the least squares calculation:
    div = 1 / (len(block) * s - r * r)
    a = (len(block) * p - q * r) * div
    b = (q * s - p * r) * div

    # convert the a and b to calculate clock offset from receiver sw time instead
    # of gps system time.
    b /= (1 + a)
    a /= (1 + a)

    for measurement in block:
        clock_offset = a * measurement.time + b

        corrected_pseudorange = measurement.pseudorange - measurement.delays
        corrected_pseudorange -= C * clock_offset

        error = corrected_pseudorange - measurement.geom_range

        print(measurement.time, error, measurement.satellite_id, file=arguments.datapoints)

        histogram[error // HISTOGRAM_RESOLUTION] += 1

    print("Found a block:")
    print("  length:", len(block))
    print("  offset:", a, "* x +", b)
    print("  time:  ", block[-1].time, "-", block[0].time, "=", (block[-1].time - block[0].time) / 60, "minutes")

def print_histogram():
    for i in sorted(histogram):
        print(i * HISTOGRAM_RESOLUTION, histogram[i], file=arguments.histogram)

setup_logging()

logger = logging.getLogger('main')

arg_parser = argparse.ArgumentParser(
    description="Calculate the UERE from recorded data.\n"
    "Assumes that the receiver was stationary during whole recording.")
arg_parser.add_argument('recording')
arg_parser.add_argument('--group', default=None, type=int,
    help="Work only with the given group in phase 3. For testing only.")
arg_parser.add_argument('--datapoints', default=open("/dev/null", "w"),
    type=argparse.FileType("w"),
    help="File into which the data points in phase 3 will go.")
arg_parser.add_argument('--histogram', default=None, type=argparse.FileType("w"),
    help="File into which the error histogram will go.")
arguments = arg_parser.parse_args()

histogram = collections.Counter()

receiver_pos = pass_one()
try:
    pass_two()
    if arguments.histogram:
        print_histogram()

except KeyboardInterrupt:
    logger.info("Terminating.")
else:
    logger.info("Done.")

