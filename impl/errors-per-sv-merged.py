#!/usr/bin/python
"""
errors-per-sv-merged.py

Plot histograms for errors of all satellites with corrected residual errors.
"""

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
    description="Plot histograms for errors of all satellites with corrected residual errors.")
arg_parser.add_argument('fixes', help="Data obtained from clock_offsets_to_numpy.py")
arg_parser.add_argument('--no-show', action='store_true',
    help="Don't show the plots, only save them.")
arg_parser.add_argument('--outlier-threshold', action='store', type=float, default=60,
    help="Error threshold for calculating the pseudorange histogram")
arg_parser.add_argument('--velocity-outlier-threshold', action='store', type=float, default=4,
    help="Error threshold for calculating the velocity histogram")
arg_parser.add_argument('--fit-window', type=float, default=2 * 60,
    help="Controls how large the window for smoothing clock offsets will be, in seconds.")
arg_parser.add_argument('--time-threshold', action='store', type=float, default=2,
    help="Time difference in seconds that is still counted as successive measurement.")
arg_parser.add_argument('--save-pseudorange-histogram', default=None,
    help="Filename, optionally followed by comma separated (x0, y0, x1, y1) coordinates.")
arg_parser.add_argument('--save-velocity-histogram', default=None,
    help="Filename, optionally followed by comma separated (x0, y0, x1, y1) coordinates.")
arg_parser.add_argument('--save-residual-drifts-derivation-histogram', default=None,
    help="Filename, optionally followed by comma separated (x0, y0, x1, y1) coordinates.")
arg_parser.add_argument('--save-clock-drifts-derivation-histogram', default=None,
    help="Filename, optionally followed by comma separated (x0, y0, x1, y1) coordinates.")
arguments = arg_parser.parse_args()

logging.info("Retreiving fixes")

data = numpy.load(arguments.fixes)

data['errors'] -= data['clock_offsets']
data['velocity_errors'] -= data['clock_drifts']

logging.info("Processing")

all_errors = numpy.array([])
all_velocity_errors = numpy.array([])
all_residual_drifts_deriv = numpy.array([])

for sv_id in numpy.unique(data['sv_ids']):
    logging.info("Processing SV ID {}".format(sv_id))
    mask = (data['sv_ids'] != sv_id)
    times = numpy.ma.array(data['times'], mask=mask).compressed()
    errors = numpy.ma.array(data['errors'], mask=mask).compressed()
    velocity_errors = numpy.ma.array(data['velocity_errors'], mask=mask).compressed()

    residual_drifts, residual_offsets = fit_clock_offsets(times, errors, arguments.fit_window)

    errors -= residual_offsets
    velocity_errors -= residual_drifts

    time_diffs = times[1:] - times[:-1]
    residual_drifts_deriv = (residual_drifts[1:] - residual_drifts[:-1]) / time_diffs
    residual_drifts_deriv = numpy.ma.array(residual_drifts_deriv, mask=time_diffs > arguments.time_threshold).compressed()

    all_errors = numpy.append(all_errors, errors)
    all_velocity_errors = numpy.append(all_velocity_errors, velocity_errors)
    all_residual_drifts_deriv = numpy.append(all_residual_drifts_deriv, residual_drifts_deriv)

time_diffs = data['times'][1:] - data['times'][:-1]

mask = numpy.logical_or(time_diffs == 0, time_diffs > arguments.time_threshold)
differences = data['clock_drifts'][1:] - data['clock_drifts'][:-1]
differences = numpy.ma.array(differences, mask = mask).compressed()
time_diffs = numpy.ma.array(time_diffs, mask = mask).compressed()
clock_drifts_deriv = differences / time_diffs

logging.info("Plotting")

error_histogram = plt.figure().add_subplot(1, 1, 1)
mu, sigma, outliers = matplotlib_settings.plot_hist(error_histogram,
                                                    all_errors,
                                                    arguments.outlier_threshold)
print("Mean: {}".format(mu))
print("Sigma: {}".format(sigma))
print("Outlier probability: {}".format(outliers))
error_histogram.set_title('Measurement errors')
error_histogram.set_xlabel(r'Error/\si{\meter}')
error_histogram.set_ylabel(r'Count')
matplotlib_settings.maybe_save_plot(error_histogram,
                                    arguments.save_pseudorange_histogram)

fig2 = plt.figure()
velocity_error_histogram = fig2.add_subplot(1, 1, 1)
mu, sigma, outliers = matplotlib_settings.plot_hist(velocity_error_histogram,
                                          all_velocity_errors,
                                          arguments.velocity_outlier_threshold)
print("Velocity mean: {}".format(mu))
print("Velocity sigma: {}".format(sigma))
print("Outlier probability: {}".format(outliers))
velocity_error_histogram.set_title('Velocity errors')
velocity_error_histogram.set_xlabel(r'Error/\si{\meter\per\second}')
velocity_error_histogram.set_ylabel(r'Count')
matplotlib_settings.maybe_save_plot(velocity_error_histogram,
                                    arguments.save_velocity_histogram)

fig3 = plt.figure()
residual_drifts_deriv_histogram = fig3.add_subplot(1, 1, 1)
mu, sigma, outliers = matplotlib_settings.plot_hist(residual_drifts_deriv_histogram,
                                                    all_residual_drifts_deriv,
                                                    1)
print("Residual clock drift derivation mean: {}".format(mu))
print("Residual clock drift derivation sigma: {}".format(sigma))
print("Outlier probability: {}".format(outliers))
residual_drifts_deriv_histogram.set_title('Clock drift derivations'.format(sv_id))
residual_drifts_deriv_histogram.set_xlabel(r'Value/\si{\meter\per\second\squared}')
residual_drifts_deriv_histogram.set_ylabel(r'Count')
matplotlib_settings.maybe_save_plot(residual_drifts_deriv_histogram,
                                    arguments.save_residual_drifts_derivation_histogram)

fig4 = plt.figure()
clock_drifts_deriv_histogram = fig4.add_subplot(1, 1, 1)
mu, sigma, outliers = matplotlib_settings.plot_hist(clock_drifts_deriv_histogram,
                                                    clock_drifts_deriv,
                                                    1)
print("Clock drift derivation mean: {}".format(mu))
print("Clock drift derivation sigma: {}".format(sigma))
print("Outlier probability: {}".format(outliers))
clock_drifts_deriv_histogram.set_title('Clock drift derivations'.format(sv_id))
clock_drifts_deriv_histogram.set_xlabel(r'Value/\si{\meter\per\second\squared}')
clock_drifts_deriv_histogram.set_ylabel(r'Count')
matplotlib_settings.maybe_save_plot(clock_drifts_deriv_histogram,
                                    arguments.save_clock_drifts_derivation_histogram)

if not arguments.no_show:
    plt.show()
