#!/usr/bin/python
"""
compare_hdop_histogram.py

Plot one or more histograms of encountered HDOP values.
"""

from __future__ import division

import matplotlib_settings
import wgs84_fixes_to_numpy

import math
import logging
import argparse
import gps
import pyproj
import numpy
import scipy.optimize
import matplotlib.pyplot as plt
import matplotlib.ticker
import itertools

logging.basicConfig(
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level = logging.INFO
)

arg_parser = argparse.ArgumentParser(
    description="Plot one or more histograms of encountered HDOP values.")
arg_parser.add_argument('sources', nargs='+',
    help="One or more recordings of SiRF messages or saved numpy arrays (*.npy).")
arg_parser.add_argument('--hist-resolution', default=0.2, type=float,
    help="Width of the histogram bin.")
arg_parser.add_argument('--save-hist-plot', default=None, type=str,
    help="Where to save the histogram plot.")
arg_parser.add_argument('--no-show', action='store_true',
    help="Don't show the plots, only save them.")
arg_parser.add_argument('--max-plot-hdop', type=float,
    help="Don't plot hdops larger than this.")
arg_parser.add_argument('--labels', action='store', default='',
    help="Labels for histograms, comma separated")
arguments = arg_parser.parse_args()

arguments.labels = arguments.labels.split(',')
arguments.labels.extend(arguments.sources[len(arguments.labels):])

fig = plt.figure()

hdops = []
max_hdop = 0
for source in arguments.sources:
    logging.info("Retrieving fixes from %s", source)
    fixes = wgs84_fixes_to_numpy.open_source(source)
    logging.info("Done. Have %i fixes", len(fixes))

    max_hdop = max(max_hdop, numpy.amax(fixes["hdop"]))
    hdops.append(fixes["hdop"])

res = arguments.hist_resolution
bins = [res * x - (res / 2) for x in range(int(math.floor(max_hdop / res) + 2))]

if arguments.max_plot_hdop is not None:
    max_hdop = arguments.max_plot_hdop

for i, (hdop, label) in enumerate(zip(hdops, arguments.labels)):
    plot = fig.add_subplot(len(hdops), 1, i + 1)
    n, _, _ = plot.hist(hdop, bins=bins, label=label, alpha=0.7)

    plot.set_xlabel("HDOP")
    plot.set_ylabel("Fix count")
    plot.locator_params(axis='x', nbins=20, integer=False)
    matplotlib_settings.common_plot_settings(plot,
        0, max_hdop,
        0, numpy.amax(n))

    if arguments.max_plot_hdop is not None:
        print("Outliers in {}:".format(label))
        for low, high, count in zip(bins[:-1], bins[1:], n):
            if high > max_hdop and count > 0:
                print("{} - {}: {}".format(low, high, count))

# Magic fiddling with sizes to make three histograms fit on a single page.
# Do not look for logic here
w, h = fig.get_size_inches()
height_multiple = 0.6 * len(hdops)
fig.set_size_inches(w, h * height_multiple)
fig.subplots_adjust(
    bottom=matplotlib_settings.m.rcParams['figure.subplot.bottom'] / 2,
    hspace=matplotlib_settings.m.rcParams['figure.subplot.hspace'])

if arguments.save_hist_plot is not None:
    fig.savefig(arguments.save_hist_plot)
    logging.info("Saved %s", arguments.save_hist_plot)

if not arguments.no_show:
    plt.show()

