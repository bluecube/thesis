#!/usr/bin/python
from __future__ import division, print_function

import argparse
import numpy
import math
import logging
import resource
import itertools

import gps
import matplotlib_settings
import matplotlib.pyplot as plt
import matplotlib
import progressbar

import util

logging.basicConfig(
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level = logging.INFO
)

CLOCK_CORRECTION_THRESHOLD = 1e6 # Distance jump in meters that is considered as clock correction.

arg_parser = argparse.ArgumentParser(
    description="Plot ")
arg_parser.add_argument('fixes', help="Data obtained from clock_offsets_to_numpy.py")
arg_parser.add_argument('--hist-resolution', default=0.2, type=float,
    help="Width of the histogram bin.")
arg_parser.add_argument('--no-show', action='store_true',
    help="Don't show the plots, only save them.")
arg_parser.add_argument('--plot-thinning', action='store', type=int, default=1,
    help="Only plot each N-th item.")
arg_parser.add_argument('--outlier-threshold', action='store', type=float, default=20,
    help="X axis scaling for histogram")
arg_parser.add_argument('--time-threshold', action='store', type=float, default=2,
    help="Time difference in seconds that is still counted as successive measurement.")
arguments = arg_parser.parse_args()

logging.info("Retreiving fixes & Fiddling")

def measurements_generator(data):
    last_states = {}
    time_threshold = arguments.time_threshold

    bar = progressbar.ProgressBar(maxval = len(data["times"]))

    for time, sv_id, error in bar(itertools.izip(data["times"], data["sv_ids"], data["errors"] - data["clock_offsets"])):
        last_time, last_error = last_states.get(
            sv_id, (time - 2 * time_threshold, None))
        time_diff = time - last_time
        if time_diff < time_threshold:
            yield time, sv_id, (error - last_error) / time_diff
        last_states[sv_id] = (time, error)

data = numpy.fromiter(
    measurements_generator(numpy.load(arguments.fixes)),
    dtype=[
        ('times', numpy.float),
        ('sv_ids', numpy.float),
        ('errors', numpy.float),
    ])

times = data["times"][::arguments.plot_thinning]
sv_ids = (data["sv_ids"] / data["sv_ids"].max())[::arguments.plot_thinning]
errors = data["errors"][::arguments.plot_thinning]

logging.info("Plotting")

fig1 = plt.figure()
error_plot = fig1.add_subplot(1, 1, 1)
error_plot.scatter(times, errors, c=sv_ids, marker='.', s=40, alpha=0.7,
    edgecolors='none', rasterized=True)
error_plot.set_title('Measurement error derivation')
error_plot.set_xlabel(r'Time/\si{\second}')
error_plot.set_ylabel(r'Error derivation/\si{\meter\per\second}')
matplotlib_settings.common_plot_settings(error_plot, set_limits=False)

fig2 = plt.figure()
error_histogram = fig2.add_subplot(1, 1, 1)
mu, sigma = matplotlib_settings.plot_hist(error_histogram,
                                          errors,
                                          arguments.hist_resolution,
                                          arguments.outlier_threshold)
print("Mean: {}".format(mu))
print("Sigma: {}".format(sigma))
error_histogram.set_title('Measurement errors')
error_histogram.set_xlabel(r'Error/\si{\meter}')
error_histogram.set_ylabel(r'Count')

if not arguments.no_show:
    plt.show()
