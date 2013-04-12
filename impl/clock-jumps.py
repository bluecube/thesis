#!/usr/bin/python
"""
clock-jumps.py

Plot clock offsets from the preprocessed data.
"""

from __future__ import division, print_function

import argparse
import numpy
import logging
import resource

import gps
from util import matplotlib_settings
import matplotlib.pyplot as plt
import matplotlib

import util

logging.basicConfig(
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level = logging.INFO
)

arg_parser = argparse.ArgumentParser(
    description="Plot clock offsets from the preprocessed data.")
arg_parser.add_argument('fixes', help="Data obtained from clock_offsets_to_numpy.py")
arg_parser.add_argument('--no-show', action='store_true',
    help="Don't show the plots, only save them.")
arg_parser.add_argument('--save-plot', default=None,
    help="Filename, optionally followed by comma separated (x0, y0, x1, y1) coordinates.")
arguments = arg_parser.parse_args()

logging.info("Retreiving fixes")

data = numpy.load(arguments.fixes)

logging.info("Plotting")

plot = plt.figure().add_subplot(1, 1, 1)
plot.plot(data['times'], data['clock_offsets'] / gps.measurement_error.C, alpha=0.7, rasterized=True)
plot.set_title('Clock offsets')
plot.set_xlabel(r'Time/\si{\second}')
plot.set_ylabel(r'Clock offset/\si{\second}')
matplotlib_settings.maybe_save_plot(plot, arguments.save_plot)

if not arguments.no_show:
    plt.show()
