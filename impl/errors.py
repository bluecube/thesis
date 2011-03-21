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
        self.c_n = msg.c_n

        self.satellite_id = msg.satellite_id

    def process(self, svs):
        """
        Because SV data come after the measurement data, we have to
        add this part after the measurement is initialized.
        Returns false if the measurement was invalid.
        """

        if self.satellite_id not in svs:
            return False

        if self.pseudorange == 0.0:
            return False

        self.process_sv(svs[self.satellite_id])
        self.process_geometry()

        self.process_delays(svs[self.satellite_id])
        self.process_corrected_pseudorange()
        self.process_raw_clock_offset()

        return True

    def process_sv(self, sv):
        """
        Handle all the calculations related to SV state.

        Sets the clock_offset_sv, sv_pos
        """
        # Time of transmission in SV clock
        time_of_transmission_sv = self.gps_sw_time - self.pseudorange / C

        # SV clock offset at the time of transmission.
        self.clock_offset_sv = ((sv.clock_bias -
            (sv.gps_time - time_of_transmission_sv) * sv.clock_drift) /
            (1 + sv.clock_drift))
        
        # Time of transmission in GPS system clock
        time_of_transmission_sys = time_of_transmission_sv - self.clock_offset_sv

        # How far is the current SV position from the position announced in MID30
        sv_pos_correction = (sv.gps_time - time_of_transmission_sys) * sv.v

        self.sv_pos = sv.pos - sv_pos_correction

        return 

    def process_geometry(self):
        """
        Handles the relative positions of user and SV.
        This is distance and SV elevation.
        """
        user_to_sv = self.sv_pos - receiver_pos

        self.geom_range = math.sqrt(user_to_sv * user_to_sv.T)

        self.elevation = math.pi / 2 - math.acos((user_to_sv * receiver_pos.T) /
            (self.geom_range * math.sqrt(receiver_pos * receiver_pos.T)))

    def process_raw_clock_offset(self):
        """
        Calculate the raw clock offset as an input for the least squares.
        This is what the clock offset would be if there was no measurement error.
        """
        self.raw_clock_offset = (self.corrected_pseudorange - self.geom_range) / C

    def process_delays(self, sv):
        self.delays = sv.iono_delay
        self.delays += self.tropo_delay()

    def process_corrected_pseudorange(self):
        self.corrected_pseudorange = (
            self.pseudorange + C * self.clock_offset_sv - self.delays)

    def tropo_delay(self):
        """
        Estimate the tropospheric delay.
        """
        elevation_squared = self.elevation * self.elevation
        return 2.312 / math.sin(math.sqrt(elevation_squared + 1.904E-3)) + \
            0.084 / math.sin(math.sqrt(elevation_squared + 0.6854E-3))

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
                    if x.process(sv):
                        yield x

                group = [measurement]
                groupTime = measurement.time
        elif isinstance(msg, NavigationLibrarySVStateData):
            sv[msg.satellite_id] = msg

    for x in group:
        if x.process(sv):
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

    drift = m2.raw_clock_offset - m1.raw_clock_offset
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

    block = [generator.__next__()]

    if not (arguments.group is None):
        logger.debug("skipping " + str(arguments.group) + " blocks")
        for i in range(arguments.group):
            for measurement in generator:
                if is_clock_correction(block[-1], measurement):
                    block = [measurement]
                    break
                else:
                    block.append(measurement)

    assert len(block) == 1

    for measurement in generator:
        offset = block[-1].raw_clock_offset
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

    offset = block[-1].raw_clock_offset
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

        error = (
            measurement.corrected_pseudorange - C * clock_offset -
            measurement.geom_range)

        print(
            measurement.time - clock_offset,
            error,
            measurement.satellite_id,
            min(measurement.c_n),
            file=arguments.datapoints)

        histogram[error // HISTOGRAM_RESOLUTION] += 1

    logger.info("Pass 3: Found a block.")
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
arg_parser.add_argument('--receiver-pos', type=numpy.matrix, default=None,
    help="Use this ECEF receiver position instead of computing it in phase 1.")
arguments = arg_parser.parse_args()

histogram = collections.Counter()

if arguments.receiver_pos is None:
    receiver_pos = pass_one()
else:
    logger.info("Skipping phase 1, because receiver pos was given.")
    receiver_pos = arguments.receiver_pos

try:
    pass_two()
    if arguments.histogram:
        print_histogram()

except KeyboardInterrupt:
    logger.info("Terminating.")
else:
    logger.info("Done.")

