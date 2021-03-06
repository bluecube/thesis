"""
matplotlib_settings.py

Common functionality for plotting and plottig style for the thesis.
To switch to the style, this file must be only imported.

Automatically detects whether to use LaTeX, or matplotlib's mathtext.
"""

from __future__ import division

import matplotlib as m
import matplotlib.ticker
import os
import numpy
import math
import logging
import matplotlib.pyplot as plt
import tempfile

m.rcParams['text.usetex'] = True
m.rcParams['text.latex.preamble'] = '\input{' + os.getcwd() + '/../text/common-style.tex}'

m.rcParams['font.size'] = 11
m.rcParams['font.family'] = 'serif'
m.rcParams['legend.fontsize'] = 11
m.rcParams['axes.labelsize'] = 11
m.rcParams['axes.labelsize'] = 11
m.rcParams['axes.titlesize'] = 11

m.rcParams['svg.fonttype'] = 'none'
m.rcParams['savefig.dpi'] = 600

m.rcParams["figure.figsize"] = '6.5, 4'
m.rcParams['figure.subplot.left'] = 0.145
m.rcParams['figure.subplot.right'] = 0.855
m.rcParams['figure.subplot.top'] = 1
m.rcParams['figure.subplot.bottom'] = 0.10
m.rcParams['figure.subplot.hspace'] = 0.3

m.rcParams['axes.grid'] = True

# Make plotting not fail in case there isn't LaTeX environment
# capable of typesetting the thesis text. In this case we should revert
# to simply using some matplotlib defaults.
fig = plt.figure()
fig.add_subplot(111).plot([1, 2, 3])
with tempfile.TemporaryFile() as f:
    try:
        fig.savefig(f)
    except RuntimeError:
        m.rcParams['text.usetex'] = False
plt.close(fig)
del fig

margins = 0.02

def ticker_format_func(x, pos):
    """Helper function providing formating of plot tickers using siunitx
    LaTeX package"""

    if x == int(x):
        x = int(x)
    return r'\num{' + str(x) + '}'

ticker_format = matplotlib.ticker.FuncFormatter(ticker_format_func)

def _settings(plot):
    """internal function used in common_plot_settings and maybe_save_plot"""

    legend = plot.legend()
    if legend is not None:
        legend.get_frame().set_alpha(0.75)

    if m.rcParams['text.usetex']:
        plot.xaxis.set_major_formatter(ticker_format)
        plot.yaxis.set_major_formatter(ticker_format)


def common_plot_settings(plot, min_x = None, max_x = None, min_y = None, max_y = None, set_limits=True):
    """Common settings for all plots in my thesis.
    Should be applied after all drawing is done."""

    _settings(plot)

    if set_limits:
        margin = (max_x - min_x) * margins
        plot.set_xlim([min_x - margin, max_x + margin])

        margin = (max_y - min_y) * margins
        plot.set_ylim([min_y - margin, max_y + margin])

def maybe_save_plot(plot, command = None):
    """Common part of saving plot.
    If command is not None, then it is expected to be a filename,
    optionally followed by comma separated coordinates (x0, y0, x1, y1)."""

    _settings(plot)

    if command is None:
        return

    command = command.split(',')
    if len(command) != 5 and len(command) != 1:
        raise ValueError("Plot saving argument must be filename optionally followed by four coordinates")

    filename = command[0]

    if len(command) == 5:
        x0, y0, x1, y1 = (float(x) for x in command[1:])

        margin = abs(x1 - x0) * margins
        plot.set_xlim([min(x0, x1) - margin, max(x0, x1) + margin])

        margin = abs(y1 - y0) * margins
        plot.set_ylim([min(y0, y1) - margin, max(y0, y1) + margin])

    plot.figure.savefig(filename)
    logging.info("Saved " + filename)

def plot_hist(subplot, data, threshold):
    """ Shared functionality of histogram plotting.
    Adds the histogram of data to subplot, returning mean, standard deviation and number of outliers.
    Threshold sets distance from the mean that separates outliers from correct data.

    Both resolution and scale are chosen automatically (based on standard deviation)."""

    masked_data = numpy.ma.array(data, mask=(numpy.abs(data) > threshold))
    mu = numpy.ma.mean(masked_data, dtype=numpy.float64)

    masked_data = numpy.ma.array(data, mask=(numpy.abs(data - mu) > threshold))
    mu = numpy.ma.mean(masked_data, dtype=numpy.float64)
    sigma = numpy.ma.std(masked_data - mu, dtype=numpy.float64)
    outliers = 1 - masked_data.count() / len(masked_data)

    threshold = 4 * sigma
    res = threshold / 50

    bin_half_count = int(math.floor(threshold * 1.05 / res))
        # extra 5% makes the histogram look a little nicer and not that cut off
    bins = [res * x - (res / 2) for x in range(-bin_half_count, bin_half_count + 2)]

    compressed = numpy.ma.array(data).compressed()
    n, bins, patches = subplot.hist(compressed, bins=bins, alpha=0.7)

    common_plot_settings(subplot,
        min_x = mu - threshold,
        max_x = mu + threshold,
        min_y = 0,
        max_y = numpy.max(n))

    return mu, sigma, outliers
