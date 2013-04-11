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

logging.basicConfig(
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level = logging.INFO
)

arg_parser = argparse.ArgumentParser(
    description="Plot ")
arg_parser.add_argument('fixes', help="Data obtained from clock_offsets_to_numpy.py")
arg_parser.add_argument('--no-show', action='store_true',
    help="Don't show the plots, only save them.")
arg_parser.add_argument('--plot-thinning', action='store', type=int, default=1,
    help="Only plot each N-th item.")
arg_parser.add_argument('--outlier-threshold', action='store', type=float, default=250,
    help="Error threshold for calculating the pseudorange histogram")
arg_parser.add_argument('--velocity-outlier-threshold', action='store', type=float, default=4,
    help="Error threshold for calculating the velocity histogram")
arg_parser.add_argument('--save-pseudorange-errors', default=None,
    help="Filename, optionally followed by comma separated (x0, y0, x1, y1) coordinates.")
arg_parser.add_argument('--save-pseudorange-histogram', default=None,
    help="Filename, optionally followed by comma separated (x0, y0, x1, y1) coordinates.")
arguments = arg_parser.parse_args()

logging.info("Retreiving fixes")

data = numpy.load(arguments.fixes)

times = data['times'][::arguments.plot_thinning]
sv_ids = (data['sv_ids'] / data['sv_ids'].max())[::arguments.plot_thinning]
errors = data['errors'][::arguments.plot_thinning]
clock_offsets = data['clock_offsets'][::arguments.plot_thinning]
clock_drifts = data['clock_drifts'][::arguments.plot_thinning]
errors -= clock_offsets
velocity_errors = data['velocity_errors'][::arguments.plot_thinning]
velocity_errors -= clock_drifts

logging.info("Plotting")

error_plot = plt.figure().add_subplot(1, 1, 1)
error_plot.scatter(times, errors, c=sv_ids, marker='.', s=40, alpha=0.7,
    edgecolors='none', rasterized=True)
error_plot.set_title('Measurement errors')
error_plot.set_xlabel(r'Time/\si{\second}')
error_plot.set_ylabel(r'Error/\si{\meter}')
matplotlib_settings.maybe_save_plot(error_plot, arguments.save_pseudorange_errors)

error_histogram = plt.figure().add_subplot(1, 1, 1)
mu, sigma, outliers = matplotlib_settings.plot_hist(error_histogram,
                                                    errors,
                                                    arguments.outlier_threshold)
print("Mean: {}".format(mu))
print("Sigma: {}".format(sigma))
error_histogram.set_title('Measurement errors')
error_histogram.set_xlabel(r'Error/\si{\meter}')
error_histogram.set_ylabel(r'Count')
matplotlib_settings.maybe_save_plot(error_histogram, arguments.save_pseudorange_histogram)

drifts_plot = plt.figure().add_subplot(1, 1, 1)
drifts_plot.plot(times, clock_drifts,
    '-', alpha=0.7)
drifts_plot.set_title('Receiver clock drifts')
drifts_plot.set_xlabel(r'Time/\si{\second}')
drifts_plot.set_ylabel(r'Drift/\si{\meter\per\second}')
matplotlib_settings.common_plot_settings(drifts_plot, set_limits=False)

velocity_plot = plt.figure().add_subplot(1, 1, 1)
velocity_plot.scatter(times,velocity_errors, c=sv_ids, marker='.', s=40, alpha=0.7,
    edgecolors='none', rasterized=True)
velocity_plot.set_title('Velocity errors')
velocity_plot.set_xlabel(r'Time/\si{\second}')
velocity_plot.set_ylabel(r'Error/\si{\meter\per\second}')
matplotlib_settings.common_plot_settings(velocity_plot, set_limits=False)


velocity_error_histogram = plt.figure().add_subplot(1, 1, 1)
mu, sigma, outliers = matplotlib_settings.plot_hist(velocity_error_histogram,
                                                    velocity_errors,
                                                    arguments.velocity_outlier_threshold)
print("Velocity mean: {}".format(mu))
print("Velocity sigma: {}".format(sigma))
velocity_error_histogram.set_title('Velocity errors')
velocity_error_histogram.set_xlabel(r'Error/\si{\meter\per\second}')
velocity_error_histogram.set_ylabel(r'Count')

if not arguments.no_show:
    plt.show()
