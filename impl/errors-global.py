#!/usr/bin/python
from __future__ import division, print_function

import argparse
import random
import numpy
import math
import logging
import resource

import gps
import matplotlib_settings
import matplotlib.pyplot as plt

logging.basicConfig(
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level = logging.INFO
)

OUTLIER_THRESHOLD = 300 # Error in meters that is considered an outlier
CLOCK_CORRECTION_THRESHOLD = 1e6 # Distance jump in meters that is considered as clock correction.

arg_parser = argparse.ArgumentParser(
    description="Calculate the UERE from recorded data.\n"
    "Assumes that the receiver was stationary during whole recording.\n"
    "Calculates clock offset from the whole recording, not just blocks between clock corrections.")
arg_parser.add_argument('gps', help="GPS receiver or recording.")
arg_parser.add_argument('--receiver-pos', type=numpy.matrix, default=None, required=True,
    help="Ground truth receiver position.")
arg_parser.add_argument('--hist-resolution', default=1, type=float,
    help="Width of the histogram bin.")
arg_parser.add_argument('--fit-degree', type=int, default=1,
    help="Degree of the polynomial estimating clock offsets.")
arg_parser.add_argument('--no-show', action='store_true',
    help="Don't show the plots, only save them.")
arg_parser.add_argument('--plot-thinning', action='store', type=int, default=1,
    help="Only plot each N-th item.")
arguments = arg_parser.parse_args()

receiver_state = gps.StationState(
    pos = arguments.receiver_pos,
    velocity = numpy.matrix([[0, 0, 0]]),
    clock_offset = 0,
    clock_drift = 0)

source = gps.open_gps(arguments.gps)
ephemeris = gps.BroadcastEphemeris()
measurements = gps.MessageCollector(gps.sirf_messages.NavigationLibraryMeasurementData)

clock_corrections = []

times = [] # Measurement times in receiver time frame
sv_ids = []
measurement_errors = []
clock_correction_values  = []
last_derivation = None
last_avg_error = None
last_time = None
unmodified_last_time = None
week_offset = 0 # offset of the current gps week from the first recorded one

def cycle_end_callback():
    global last_avg_error
    global last_time
    global unmodified_last_time
    global last_derivation
    global week_offset

    count = 0
    error_sum = 0

    cycle_start = len(measurement_errors)

    if len(measurements.collected) == 0:
        return

    if measurements.collected[0].gps_sw_time < unmodified_last_time:
        week_offset += 7 * 24 * 3600

    for measurement in measurements.collected:
        me = gps.MeasurementError(ephemeris)
        if not me.set_measurement(measurement):
            continue
        me.set_receiver_state(receiver_state)

        error = me.pseudorange_error()

        count += 1
        error_sum += error
        times.append(measurement.gps_sw_time + week_offset)
        unmodified_last_time = measurement.gps_sw_time
        sv_ids.append(measurement.satellite_id)
        measurement_errors.append(error)

    if not count:
        return

    avg_error = error_sum / count

    if last_avg_error is None:
        # This is the first record
        current_clock_correction = 0
    else:
        time_diff = times[-1] - last_time
        assert time_diff > 0

        error_diff = avg_error - last_avg_error
        derivation = error_diff / time_diff # unit: meter / receiver_second

        #sys_time_diff = time_diff - (clock_offset(times[-1]) - clock_offset(last_time))
        #new_sys_derivation = error_diff / sys_time_diff # unit: meter / second

        if abs(derivation) > CLOCK_CORRECTION_THRESHOLD:
            # This is clock correction

            clock_corrections.append(cycle_start)

            correction_magnitude = error_diff - last_derivation * time_diff
            current_clock_correction = clock_correction_values[-1] - correction_magnitude
        else:
            current_clock_correction = clock_correction_values[-1]
            last_derivation = derivation

    clock_correction_values.extend(count * [current_clock_correction])
    last_avg_error = avg_error
    last_time = times[-1]

    measurements.clear()

try:
    source.loop([ephemeris, measurements], cycle_end_callback)
except KeyboardInterrupt:
    pass

logging.info("Processing...")

cycle_end_callback() # Last cycle doesn't end, so this wouldn't be otherwise called.

logging.info("- Convert to arrays...")
times = numpy.array(times, dtype=numpy.float)
sv_ids = numpy.array(sv_ids, dtype=numpy.float)
measurement_errors = numpy.array(measurement_errors, dtype=numpy.float)
clock_correction_values = numpy.array(clock_correction_values, dtype=numpy.float)

logging.info("- Fit clock corrections...")

poly = numpy.polynomial.polynomial.Polynomial.fit(
    times, measurement_errors + clock_correction_values, deg = arguments.fit_degree)

clock_offsets = poly(times) - clock_correction_values

measurement_errors -= clock_offsets
#system_times = times - clock_offsets / gps.C

sv_ids /= sv_ids.max()

logging.info("- Free some memory...")

rss_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

del clock_correction_values
del clock_offsets
del ephemeris
del measurements
del source

rss_saved = rss_before - resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

logging.info("    Freed {} kB".format(rss_saved))

logging.info("Plot...")

fig1 = plt.figure()
error_plot = fig1.add_subplot(1, 1, 1)

error_plot.scatter(times[::arguments.plot_thinning], measurement_errors[::arguments.plot_thinning],
    c=sv_ids[::arguments.plot_thinning], marker='.', s=40, alpha=0.7, edgecolors='none',rasterized=True)
for index in clock_corrections:
    error_plot.axvline(times[index], color='b', alpha=0.5)
error_plot.set_title('Measurement errors')
error_plot.set_xlabel(r'Time [\si{\second}]')
error_plot.set_ylabel(r'Error [\si{\meter}]')
matplotlib_settings.common_plot_settings(error_plot, set_limits=False)

res = arguments.hist_resolution
bin_half_count = int(math.floor(1.05 * OUTLIER_THRESHOLD / res))
    # extra 5% makes the histogram look a little nicer and not that cut off
bins = [res * x - (res / 2) for x in range(-bin_half_count, bin_half_count + 2)]
fig2 = plt.figure()
error_histogram = fig2.add_subplot(1, 1, 1)
n, bins, patches = error_histogram.hist(measurement_errors, bins=bins, alpha=0.7)
error_histogram.set_title('Measurement errors')
error_histogram.set_xlabel(r'Error [\si{\meter}]')
error_histogram.set_ylabel(r'Count')
matplotlib_settings.common_plot_settings(error_histogram,
    min_x = -OUTLIER_THRESHOLD,
    max_x = OUTLIER_THRESHOLD,
    min_y = 0,
    max_y = numpy.max(n))

#fig3 = plt.figure()
#offsets_plot = fig3.add_subplot(1, 1, 1)
#offsets_plot.plot(times, clock_offsets, label="Clock offset (from system time)")
#offsets_plot.plot(times, clock_correction_values, label="Clock corrections")
#matplotlib_settings.common_plot_settings(offsets_plot, set_limits=False)
#offsets_plot.set_xlabel(r'GPS Software time [\si{\second}]')
#offsets_plot.set_ylabel(r'[\si{\meter}]')

if not arguments.no_show:
    plt.show()
