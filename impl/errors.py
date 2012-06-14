#!/usr/bin/python

from __future__ import division, print_function

import logging
import numpy
import numpy.ma
import math
import argparse
import itertools

import gps.gps_replay
import stats

from pprint import pprint

from gps.sirf_messages import *

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.mlab

plot_time = numpy.array([])
plot_error = numpy.array([])
plot_sat_id = numpy.array([], dtype=numpy.uint8)

C = 299792458
    # Speed of light

MAX_CLOCK_DRIFT = 1e-2
    # This is a maximum clock drift (in absolute value) between two
    # measurement blocks before we call it a clock correction

OUTLIER_THRESHOLD_METERS = 100
    # Distance in meters from the average clock offset of a group
    # that is assumed an outlier.

OUTLIER_THRESHOLD = OUTLIER_THRESHOLD_METERS / C
    # Like OUTLIER_THRESHOLD_METERS, but in seconds

FIT_DEGREE = 1
    # Degree of the polynomial used for clock offset fitting.
       
class Measurement:
    """
    A single measurement of the user to sv distance, speed, ....
    """

    DTYPE = numpy.dtype([
        ('time', numpy.float64),
        ('raw_clock_offset', numpy.float64),
        ('corrected_pseudorange', numpy.float64),
        ('geom_range', numpy.float64),
        ('satellite_id', numpy.uint8)])

    def __init__(self, msg):
        self.gps_sw_time = msg.gps_sw_time
        self.pseudorange = msg.pseudorange
        self.time = msg.gps_sw_time
        self.c_n = msg.c_n

        self.satellite_id = msg.satellite_id

    def to_tuple(self):
        """
        Return tuple suitable for inserting to numpy
        array with type self.dtype().
        """
        return tuple((getattr(self, x) for x in self.DTYPE.names))

    def process(self, svs):
        """
        Because SV data come after the measurement data, we have to
        add this part after the measurement is initialized.
        Returns false if the measurement was invalid.
        """

        if self.satellite_id not in svs:
            self.valid = False
            return

        if self.pseudorange == 0.0:
            self.valid = False
            return

        self.process_sv(svs[self.satellite_id])
        self.process_geometry()

        self.process_delays(svs[self.satellite_id])
        self.process_corrected_pseudorange()
        self.process_raw_clock_offset()

        self.valid = True

    def process_sv(self, sv):
        """
        Handle all the calculations related to SV state.

        Sets the clock_offset_sv, sv_pos
        """
        # Time of transmission in SV clock
        time_of_transmission_sv = self.gps_sw_time - self.pseudorange / C

        # SV clock offset at the time of transmission.
        self.clock_offset_sv = ((sv.clock_bias +
            (time_of_transmission_sv - sv.gps_time) * sv.clock_drift)) /
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
        user_to_sv = self.sv_pos - arguments.receiver_pos

        self.geom_range = math.sqrt(user_to_sv * user_to_sv.T)

        self.elevation = math.asin((user_to_sv * arguments.receiver_pos.T) /
            (self.geom_range * math.sqrt(arguments.receiver_pos * arguments.receiver_pos.T)))

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
    Yields measurements groups.
    Measurement groups are lists of measurements that happened at the same time (this is SIRF trick
    -- in reality measurements are taken at random (?) times.
    """

    replay = gps.gps_replay.GpsReplay(arguments.recording)
    sv = {}

    group = []
    groupTime = None

    clock_status = None

    for msg in replay:
        if isinstance(msg, NavigationLibraryMeasurementData):
            measurement = Measurement(msg)

            if groupTime == measurement.time:
                group.append(measurement)
            else:
                if len(group):
                    for x in group:
                        x.process(sv)
                    yield (group, clock_status)

                group = [measurement]
                groupTime = measurement.time
        elif isinstance(msg, NavigationLibrarySVStateData):
            sv[msg.satellite_id] = msg
        elif isinstance(msg, ClockStatusData):
            clock_status = msg

    if len(group):
        for x in group:
            x.process(sv)
        yield (group, clock_status)

def get_drift(m1, m2):
    """
    Calculate clock drift between two measurement blocks.
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


def split_to_blocks():
    """
    Splits the measurements into blocks between clock corrections,
    calculates the least squares on the blocks and process every block.
    """
    logger.info("Splitting to blocks.")

    generator = measurement_generator()

    block = []
    last_measurement = None

    if arguments.sirf_clock_offsets:
        raise Exception("Sirf clock offsets are not implemented")
#        for (group, clock_status) in generator:
# 
#            for measurement in group:
#                if not measurement.valid:
#                    continue
#                process_measurement_error(measurement, clock_status.clock_bias * 1e-9)
#
#        return

    for (group, clock_status) in generator:
        filtered = [measurement for measurement in group if measurement.valid]

        if len(block) and is_clock_correction(last_measurement, filtered[-1]):
            process_block(block)
            block = []

        for measurement in filtered:
            block.append(measurement.to_tuple())
            last_measurement = measurement

    process_block(block)

def process_block(block):
    """
    Do the least squares and the main error calculations.
    """

    global plot_time
    global plot_error
    global plot_sat_id

    block = numpy.array(block, Measurement.DTYPE)

    poly = numpy.polyfit(block['time'], block['raw_clock_offset'], deg = FIT_DEGREE)
    clock_offsets = numpy.polyval(poly, block['time'])

    differences = clock_offsets - block['raw_clock_offset']

    # Mask outliers and do the fitting once more
    masked_differences = numpy.ma.masked_outside(differences, -OUTLIER_THRESHOLD, OUTLIER_THRESHOLD)
    masked_times = numpy.ma.masked_array(block['time'], mask=masked_differences.mask)

    poly = numpy.ma.polyfit(masked_times, block['raw_clock_offset'], deg = FIT_DEGREE)
    clock_offsets = numpy.polyval(poly, block['time'])

    errors = block['corrected_pseudorange'] - block['geom_range'] - C * clock_offsets

    plot_time = numpy.concatenate((plot_time, block['time']))
    plot_error = numpy.concatenate((plot_error, errors))
    plot_sat_id = numpy.concatenate((plot_sat_id, block['satellite_id']))

    logger.info("Found a block.")
    print("  length:   {}".format(len(block)))
    print("  outliers: {}".format(numpy.ma.count_masked(masked_times)))
    print("  offset:   {}".format(poly))
    print("  time:     {}-{} = {} minutes".format(block[-1][0], block[0][0], (block[-1][0] - block[0][0]) / 60))

setup_logging()

logger = logging.getLogger('main')

arg_parser = argparse.ArgumentParser(
    description="Calculate the UERE from recorded data.\n"
    "Assumes that the receiver was stationary during whole recording.")
arg_parser.add_argument('recording')
arg_parser.add_argument('--receiver-pos', type=numpy.matrix, default=None, required=True,
    help="Ground truth receiver position.")
arg_parser.add_argument('--precision', default=1000, type=int,
    help="Multiplier for fixed point arithmetic.")
arg_parser.add_argument('--hist-resolution', default=1, type=float,
    help="Width of the histogram bin.")
arg_parser.add_argument('--sirf-clock-offsets', default=False, action='store_true',
    help="Use clock offsets from sirf messages instead of calculating them.")
arguments = arg_parser.parse_args()

try:
    split_to_blocks()

except KeyboardInterrupt:
    logger.info("Terminating.")
else:
    logger.info("Done.")


sat_id = plot_sat_id / float(plot_sat_id.max())

fig1 = plt.figure()
error_plot = fig1.add_subplot(1, 1, 1)
error_plot.scatter(plot_time, plot_error, c=sat_id, marker='.', s=40, alpha=0.75, edgecolors='none')
error_plot.set_title('Measurement errors')
error_plot.set_xlabel('time [s]')
error_plot.set_ylabel('error [m]')
error_plot.grid(True)

mu = numpy.mean(plot_error)
sigma = numpy.std(plot_error)

fig2 = plt.figure()
histogram = fig2.add_subplot(1, 1, 1)
n, bins, patches = histogram.hist(plot_error, bins=100, normed=True, alpha=0.75, range=(-OUTLIER_THRESHOLD_METERS, OUTLIER_THRESHOLD_METERS))
bincenters = 0.5 * (bins[1:] + bins[:-1])
y = matplotlib.mlab.normpdf(bincenters, mu, sigma)
histogram.plot(bincenters, y, 'r--')
histogram.set_title('Histogram of measurement errors without outliers\n' + r'$\mu={}, \ \sigma={}$'.format(mu, sigma))
histogram.set_xlabel('error [m]')
histogram.set_ylabel('probability')
histogram.grid(True)

plt.show()
