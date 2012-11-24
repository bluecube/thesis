#!/usr/bin/python
from __future__ import division, print_function

import argparse
import random
import numpy
import math
import logging

import gps
import matplotlib_settings
import matplotlib.pyplot as plt

logging.basicConfig(
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level = logging.INFO
)

OUTLIER_THRESHOLD = 300

arg_parser = argparse.ArgumentParser(
    description="Calculate the UERE from recorded data.\n"
    "Assumes that the receiver was stationary during whole recording.")
arg_parser.add_argument('gps', help="GPS receiver or recording.")
arg_parser.add_argument('--receiver-pos', type=numpy.matrix, default=None, required=True,
    help="Ground truth receiver position.")
arg_parser.add_argument('--hist-resolution', default=1, type=float,
    help="Width of the histogram bin.")
arg_parser.add_argument('--fit-degree', type=int, default=2,
    help="Degree of the polynomial estimating clock offsets.")
arg_parser.add_argument('--no-show', action='store_true',
    help="Don't show the plots, only save them.")
arguments = arg_parser.parse_args()

class ReceiverState:
    """ Class that assumes the receiver stationary and estimates its clock drift
    based on raw clock offsets."""

    _velocity = numpy.matrix([[0, 0, 0]])

    def __init__(self, receiver_pos, fit_degree, clock_correction_threshold):
        """ Initialize the receiver state estimator.

        receiver pos
            is a 3x1 numpy matrix containing estimate position of the
            receiver (it has to be static during the whole recording).

        fit_degree
            Degree of the polynomial for fitting clock offsets.

        clock_correction_threshold
            If clock offset changes more than this between two epochs,
            it is considered as a clock correction and causes start of a
            new block. """

        self.pos = receiver_pos
        self._fit_degree = fit_degree
        self._clock_correction_threshold = clock_correction_threshold

        self._gps_times = []
        self._clock_offsets = []

        self._last_avg_offset = None

    def receiver_state(self, time):
        """ Return estimated receiver state in the given time.
        In contrast to the ephemeris classes time is NOT system time, but receiver time."""
        return gps.StationState(
            pos = self.pos,
            velocity = self._velocity,
            clock_offset = self._clock_offset_poly(time),
            clock_drift = self._clock_drift_poly(time))

    def add_clock_offsets(self, gps_time, offsets):
        """ Add a list of clock offsets recorded at given time for processing.

        If this batch of offsets starts a new block, then finalize is called and
        True returned. In this case the offsets in this batch are kept buffered
        for a next block.

        If the batch belongs to the currently running block, then
        this function returns False. """

        avg_offset = math.fsum(offsets) / len(offsets)

        assert not len(self._gps_times) or gps_time > self._gps_times[-1]

        is_clock_correction = (
            self._last_avg_offset is not None and
            abs(self._last_avg_offset - avg_offset) > self._clock_correction_threshold)
        self._last_avg_offset = avg_offset

        if is_clock_correction:
            self._finalize()
            self._gps_times = []
            self._clock_offsets = []

        self._gps_times.extend([gps_time] * len(offsets))
        self._clock_offsets.extend(offsets)

        return is_clock_correction

    def _finalize(self):
        """ Finalize the block (between two receiver clock corrections),
        recalculate the polynomial for receiver clock offset. """

        times = numpy.array(self._gps_times)
        offsets = numpy.array(self._clock_offsets)

        poly = numpy.polynomial.polynomial.Polynomial.fit(
            times, offsets, deg = self._fit_degree)

        mask = numpy.abs(offsets - poly(times)) > OUTLIER_THRESHOLD

        masked_times = numpy.ma.masked_array(times, mask = mask)
        masked_offsets = numpy.ma.masked_array(offsets, mask = mask)

        self._clock_offset_poly = numpy.polynomial.polynomial.Polynomial.fit(
            masked_times, masked_offsets, deg = self._fit_degree)
        self._clock_drift_poly = self._clock_offset_poly.deriv()

source = gps.open_gps(arguments.gps)
ephemeris = gps.BroadcastEphemeris()
measurements = gps.MessageCollector(gps.sirf_messages.NavigationLibraryMeasurementData)
receiver_state = ReceiverState(
    arguments.receiver_pos,
    arguments.fit_degree,
    0.05)

# Buffer for measurement errors waiting for completed receiver state
measurement_error_buffer = []

plot_times = []
plot_sv_ids = []
plot_errors = []
plot_clock_corrections = []

def top_level_cycle_end_callback():
    global measurement_error_buffer

    tmp_measurement_error_buffer = []
    offsets = []
    for measurement in measurements.collected:
        me = gps.MeasurementError(ephemeris)
        offset = me.receiver_clock_offset(measurement, arguments.receiver_pos)

        if offset is None:
            continue

        offsets.append(offset)
        tmp_measurement_error_buffer.append(me)

    if not len(measurements.collected):
        return

    is_clock_correction = receiver_state.add_clock_offsets(
        measurements.collected[0].gps_sw_time,
        offsets)


    if is_clock_correction:
        block_end()

    measurement_error_buffer.extend(tmp_measurement_error_buffer)

    measurements.clear()

def block_end():
    global measurement_error_buffer

    logging.info("processing block")

    for me in measurement_error_buffer:
        measurement = me._measurement
        receiver_time = measurement.gps_sw_time
        state = receiver_state.receiver_state(receiver_time)
        me.set_receiver_state(state)

        sys_time = receiver_time - state.clock_offset

        plot_times.append(sys_time)
        plot_errors.append(me.pseudorange_error())
        plot_sv_ids.append(measurement.satellite_id)

    plot_clock_corrections.append(sys_time)

    measurement_error_buffer = []

source.loop([ephemeris, measurements], top_level_cycle_end_callback)
#handle the last block:
receiver_state._finalize()
block_end()

plot_times = numpy.array(plot_times)
plot_errors = numpy.array(plot_errors)
plot_sv_ids = numpy.array(plot_sv_ids, dtype=numpy.float)
plot_sv_ids /= plot_sv_ids.max()


fig1 = plt.figure()
error_plot = fig1.add_subplot(1, 1, 1)
error_plot.scatter(plot_times, plot_errors,
    c=plot_sv_ids, marker='.', s=40, alpha=0.7, edgecolors='none',rasterized=True)
for x in plot_clock_corrections[:-1]:
    error_plot.axvline(x, color='b', alpha=0.5)
error_plot.set_title('Measurement errors')
error_plot.set_xlabel('time [s]')
error_plot.set_ylabel(r'Error [\si{\meter}]')
matplotlib_settings.common_plot_settings(error_plot, set_limits=False)

res = arguments.hist_resolution
bin_half_count = int(math.floor(1.05 * OUTLIER_THRESHOLD / res))
    # extra 5% makes the histogram look a little nicer and not that cut off
bins = [res * x - (res / 2) for x in range(-bin_half_count, bin_half_count + 2)]
fig2 = plt.figure()
error_histogram = fig2.add_subplot(1, 1, 1)
n, bins, patches = error_histogram.hist(plot_errors, bins=bins, alpha=0.7)
error_histogram.set_title('Measurement errors')
error_histogram.set_xlabel(r'Error [\si{\meter}]')
error_histogram.set_ylabel(r'Count')
matplotlib_settings.common_plot_settings(error_histogram,
    min_x = -OUTLIER_THRESHOLD,
    max_x = OUTLIER_THRESHOLD,
    min_y = 0,
    max_y = numpy.max(n))

if not arguments.no_show:
    plt.show()
