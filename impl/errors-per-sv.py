#!/usr/bin/python
from __future__ import division, print_function

import argparse
import numpy
import math
import logging
import resource

import gps
import matplotlib_settings
import matplotlib.pyplot as plt
import matplotlib

import util

def fit_clock_offsets(x, y, width):
    drifts, offsets = util.windowed_least_squares(x, y, width)

    del drifts
    mask = numpy.abs(y - offsets) > arguments.outlier_threshold
    del offsets

    return util.windowed_least_squares(x, y, width, mask)

logging.basicConfig(
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level = logging.INFO
)

arg_parser = argparse.ArgumentParser(
    description="Equivalent of errors_global, but only for a single SV. The clock"
    "offset fitting here should cancel most residual errors for the channel.")
arg_parser.add_argument('fixes', help="Data obtained from clock_offsets_to_numpy.py")
arg_parser.add_argument('--only-sv', action='store', type=int, required=True,
    help="Which SV to process")
arg_parser.add_argument('--no-show', action='store_true',
    help="Don't show the plots, only save them.")
arg_parser.add_argument('--plot-thinning', action='store', type=int, default=1,
    help="Only plot each N-th item.")
arg_parser.add_argument('--outlier-threshold', action='store', type=float, default=150,
    help="Threshoold for fitting clock offsets")
arg_parser.add_argument('--velocity-outlier-threshold', action='store', type=float, default=4,
    help="X axis scaling for velocity error histogram")
arg_parser.add_argument('--fit-window', type=float, default=2 * 60,
    help="Controls how large the window for smoothing clock offsets will be, in seconds.")
arg_parser.add_argument('--time-threshold', action='store', type=float, default=2,
    help="Time difference in seconds that is still counted as successive measurement.")
arguments = arg_parser.parse_args()

logging.info("Retreiving fixes")

data = numpy.load(arguments.fixes)

times = data['times']
sv_ids = data['sv_ids']
errors = data['errors'] + data['clock_corrections']
velocity_errors = data['velocity_errors']

logging.info("Processing")
if not arguments.only_sv in numpy.unique(sv_ids):
    raise ValueError("This SV id is not usable")

sv_id = arguments.only_sv
mask = (sv_ids != sv_id)
times = numpy.ma.array(times, mask=mask).compressed()
errors = numpy.ma.array(errors, mask=mask).compressed()
velocity_errors = numpy.ma.array(velocity_errors, mask=mask).compressed()

clock_drifts, clock_offsets = fit_clock_offsets(times, errors, arguments.fit_window)

errors -= clock_offsets
velocity_errors -= clock_drifts

time_diffs = times[1:] - times[:-1]
clock_drifts_deriv = (clock_drifts[1:] - clock_drifts[:-1]) / time_diffs
clock_drifts_deriv = numpy.ma.array(clock_drifts_deriv, mask=time_diffs > arguments.time_threshold).compressed()


logging.info("Plotting")

fig1 = plt.figure()
error_plot = fig1.add_subplot(1, 1, 1)
error_plot.scatter(times[::arguments.plot_thinning], errors[::arguments.plot_thinning],
    marker='.', s=40, alpha=0.7, edgecolors='none', rasterized=True)
error_plot.set_title('Measurement errors for SV {}'.format(sv_id))
error_plot.set_xlabel(r'Time/\si{\second}')
error_plot.set_ylabel(r'Error/\si{\meter}')
matplotlib_settings.common_plot_settings(error_plot, set_limits=False)

fig2 = plt.figure()
error_histogram = fig2.add_subplot(1, 1, 1)
mu, sigma, offsets = matplotlib_settings.plot_hist(error_histogram,
                                                   errors,
                                                   arguments.outlier_threshold)
print("Mean: {}".format(mu))
print("Sigma: {}".format(sigma))
error_histogram.set_title('Measurement errors for SV {}'.format(sv_id))
error_histogram.set_xlabel(r'Error/\si{\meter}')
error_histogram.set_ylabel(r'Count')

fig3 = plt.figure()
drifts_plot = fig3.add_subplot(1, 1, 1)
drifts_plot.plot(times[::arguments.plot_thinning], clock_drifts[::arguments.plot_thinning],
    '-', alpha=0.7)
drifts_plot.set_title('Receiver clock drifts for SV {}'.format(sv_id))
drifts_plot.set_xlabel(r'Time/\si{\second}')
drifts_plot.set_ylabel(r'Drift/\si{\meter\per\second}')
matplotlib_settings.common_plot_settings(drifts_plot, set_limits=False)

fig4 = plt.figure()
velocity_plot = fig4.add_subplot(1, 1, 1)
velocity_plot.scatter(times[::arguments.plot_thinning], velocity_errors[::arguments.plot_thinning],
    marker='.', s=40, alpha=0.7, edgecolors='none', rasterized=True)
velocity_plot.set_title('Velocity errors for SV {}'.format(sv_id))
velocity_plot.set_xlabel(r'Time/\si{\second}')
velocity_plot.set_ylabel(r'Error/\si{\meter\per\second}')
matplotlib_settings.common_plot_settings(velocity_plot, set_limits=False)


fig5 = plt.figure()
velocity_error_histogram = fig5.add_subplot(1, 1, 1)
mu, sigma, offset = matplotlib_settings.plot_hist(velocity_error_histogram,
                                                  velocity_errors,
                                                  arguments.velocity_outlier_threshold)
print("Velocity mean: {}".format(mu))
print("Velocity sigma: {}".format(sigma))
velocity_error_histogram.set_title('Velocity errors for SV {}'.format(sv_id))
velocity_error_histogram.set_xlabel(r'Error/\si{\meter\per\second}')
velocity_error_histogram.set_ylabel(r'Count')

fig6 = plt.figure()
clock_drifts_deriv_histogram = fig6.add_subplot(1, 1, 1)
mu, sigma, offset = matplotlib_settings.plot_hist(clock_drifts_deriv_histogram,
                                                  clock_drifts_deriv,
                                                  1)
print("Clock drift derivation mean: {}".format(mu))
print("Clock drift derivation sigma: {}".format(sigma))
clock_drifts_deriv_histogram.set_title('Clock drift derivations for SV {}'.format(sv_id))
clock_drifts_deriv_histogram.set_xlabel(r'Value/\si{\meter\per\second\squared}')
clock_drifts_deriv_histogram.set_ylabel(r'Count')

if not arguments.no_show:
    plt.show()
