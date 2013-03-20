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

CLOCK_CORRECTION_THRESHOLD = 1e6 # Distance jump in meters that is considered as clock correction.

arg_parser = argparse.ArgumentParser(
    description="Plot ")
arg_parser.add_argument('fixes', help="Data obtained from clock_offsets_to_numpy.py")
arg_parser.add_argument('--hist-resolution', default=1, type=float,
    help="Width of the histogram bin.")
arg_parser.add_argument('--velocity-hist-resolution', default=0.05, type=float,
    help="Width of the velocity histogram bin.")
arg_parser.add_argument('--no-show', action='store_true',
    help="Don't show the plots, only save them.")
arg_parser.add_argument('--plot-thinning', action='store', type=int, default=1,
    help="Only plot each N-th item.")
arg_parser.add_argument('--outlier-threshold', action='store', type=float, default=250,
    help="X axis scaling for histogram")
arg_parser.add_argument('--velocity-outlier-threshold', action='store', type=float, default=4,
    help="X axis scaling for velocity error histogram")
arg_parser.add_argument('--only-sv', action='append', type=int, default=None,
    help="X axis scaling for velocity error histogram")
arguments = arg_parser.parse_args()

logging.info("Retreiving fixes")

data = numpy.load(arguments.fixes)

times = data['times'][::arguments.plot_thinning]
sv_ids = data['sv_ids'][::arguments.plot_thinning]
errors = data['errors'][::arguments.plot_thinning]- data['clock_offsets'][::arguments.plot_thinning]

logging.info("Processing")
available_sv_ids = set(numpy.unique(sv_ids))
if arguments.only_sv is not None:
    selected_sv_ids = []
    for sv_id in set(arguments.only_sv):
        if sv_id not in available_sv_ids:
            logging.warning("SV id {} is not available, skipping".format(sv_id))
            continue
        selected_sv_ids.append(sv_id)
    selected_sv_ids.sort()
else:
    selected_sv_ids = sorted(available_sv_ids)

logging.info("Plotting")

for sv_id in selected_sv_ids:
    fig = plt.figure()
    plot = fig.add_subplot(1, 1, 1)
    mask = sv_ids != sv_id

    mu, sigma = matplotlib_settings.plot_hist(plot,
        numpy.ma.array(errors, mask=mask),
        arguments.hist_resolution,
        arguments.outlier_threshold)

    print("SV ID {}".format(sv_id))

    print("Mean: {}".format(mu))
    print("Sigma: {}".format(sigma))
    plot.set_title('Measurement errors for SV ID {}'.format(sv_id))
    plot.set_xlabel(r'Error/\si{\meter}')
    plot.set_ylabel(r'Count')

if not arguments.no_show:
    plt.show()
