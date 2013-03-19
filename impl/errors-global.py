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
import matplotlib

import util

logging.basicConfig(
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level = logging.INFO
)

CLOCK_CORRECTION_THRESHOLD = 1e6 # Distance jump in meters that is considered as clock correction.

arg_parser = argparse.ArgumentParser(
    description="Plot ")
arg_parser.add_argument('fixes', help="Data obtained from clock_offsets_to_numpy.py")
arg_parser.add_argument('--hist-resolution', default=1, type=float,
    help="Width of the histogram bin.")
arg_parser.add_argument('--no-show', action='store_true',
    help="Don't show the plots, only save them.")
arg_parser.add_argument('--plot-thinning', action='store', type=int, default=1,
    help="Only plot each N-th item.")
arg_parser.add_argument('--outlier-threshold', action='store', type=float, default=250,
    help="X axis scaling for histogram")
arguments = arg_parser.parse_args()

logging.info("Retreiving fixes")

data = numpy.load(arguments.fixes)

mu = numpy.mean(data['errors'])
sigma = numpy.std(data['errors'])
print("Mean: {}".format(mu))
print("Sigma: {}".format(sigma))

times = data['times'][::arguments.plot_thinning]
sv_ids = (data['sv_ids'] / data['sv_ids'].max())[::arguments.plot_thinning]
errors = data['errors'][::arguments.plot_thinning]
clock_offsets = data['clock_offsets'][::arguments.plot_thinning]
clock_drifts = data['clock_drifts'][::arguments.plot_thinning]
errors -= clock_offsets
velocity_errors = data['velocity_errors'][::arguments.plot_thinning]
velocity_errors -= clock_drifts

logging.info("Plotting")

fig1 = plt.figure()
error_plot = fig1.add_subplot(1, 1, 1)
error_plot.scatter(times, errors, c=sv_ids, marker='.', s=40, alpha=0.7,
    edgecolors='none', rasterized=True)
error_plot.set_title('Measurement errors')
error_plot.set_xlabel(r'Time/\si{\second}')
error_plot.set_ylabel(r'Error/\si{\meter}')
matplotlib_settings.common_plot_settings(error_plot, set_limits=False)

res = arguments.hist_resolution
bin_half_count = int(math.floor(arguments.outlier_threshold * 1.05 / res))
    # extra 5% makes the histogram look a little nicer and not that cut off
bins = [res * x - (res / 2) for x in range(-bin_half_count, bin_half_count + 2)]
fig2 = plt.figure()
error_histogram = fig2.add_subplot(1, 1, 1)
n, bins, patches = error_histogram.hist(data['errors'], bins=bins, alpha=0.7)

bincenters = 0.5 * (bins[1:] + bins[:-1])
y = matplotlib.mlab.normpdf(bincenters, mu, sigma) * len(data['errors'])
error_histogram.plot(bincenters, y, 'r--')

error_histogram.set_title('Measurement errors')
error_histogram.set_xlabel(r'Error/\si{\meter}')
error_histogram.set_ylabel(r'Count')
matplotlib_settings.common_plot_settings(error_histogram,
    min_x = -arguments.outlier_threshold,
    max_x = arguments.outlier_threshold,
    min_y = 0,
    max_y = numpy.max(n))

fig3 = plt.figure()
drifts_plot = fig3.add_subplot(1, 1, 1)
drifts_plot.plot(times, clock_drifts,
    '-', alpha=0.7)
drifts_plot.set_title('Receiver clock drifts')
drifts_plot.set_xlabel(r'Time/\si{\second}')
drifts_plot.set_ylabel(r'Drift/\si{\meter\per\second}')
matplotlib_settings.common_plot_settings(drifts_plot, set_limits=False)

#fig3 = plt.figure()
#offsets_plot = fig3.add_subplot(1, 1, 1)
#offsets_plot.plot(times, clock_offsets, label="Clock offset (from system time)")
#offsets_plot.plot(times, clock_correction_values, label="Clock corrections")
#matplotlib_settings.common_plot_settings(offsets_plot, set_limits=False)
#offsets_plot.set_xlabel(r'GPS Software time [\si{\second}]')
#offsets_plot.set_ylabel(r'[\si{\meter}]')

fig4 = plt.figure()
velocity_plot = fig4.add_subplot(1, 1, 1)
velocity_plot.scatter(times,velocity_errors, c=sv_ids, marker='.', s=40, alpha=0.7,
    edgecolors='none', rasterized=True)
velocity_plot.set_title('Velocity errors')
velocity_plot.set_xlabel(r'Time/\si{\second}')
velocity_plot.set_ylabel(r'Error/\si{\meter\per\second}')
matplotlib_settings.common_plot_settings(velocity_plot, set_limits=False)


if not arguments.no_show:
    plt.show()
