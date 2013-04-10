from __future__ import division

import matplotlib as m
import matplotlib.ticker
import os
import numpy
import math

#m.rcParams['axes.unicode_minus'] = False
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

margins = 0.02

def ticker_format_func(x, pos):
    if x == int(x):
        x = int(x)
    return r'\num{' + str(x) + '}'

ticker_format = matplotlib.ticker.FuncFormatter(ticker_format_func)


def common_plot_settings(plot, min_x = None, max_x = None, min_y = None, max_y = None, set_limits=True):
    """Common settings for all plots in my thesis.
    Should be applied after all drawing is done."""

    legend = plot.legend()
    if legend is not None:
        legend.get_frame().set_alpha(0.75)

    plot.xaxis.set_major_formatter(ticker_format)
    plot.yaxis.set_major_formatter(ticker_format)

    if set_limits:
        margin = (max_x - min_x) * margins
        plot.set_xlim([min_x - margin, max_x + margin])

        margin = (max_y - min_y) * margins
        plot.set_ylim([min_y - margin, max_y + margin])

def plot_hist(subplot, data, threshold):
    masked_data = numpy.ma.array(data, mask=(numpy.abs(data) > threshold))
    mu = numpy.ma.mean(masked_data)

    masked_data = numpy.ma.array(data, mask=(numpy.abs(data - mu) > threshold))
    mu = numpy.ma.mean(masked_data)
    sigma = numpy.ma.std(masked_data - mu)
    outliers = 1 - masked_data.count() / len(masked_data)

    threshold = 4 * sigma
    res = threshold / 100

    bin_half_count = int(math.floor(threshold * 1.05 / res))
        # extra 5% makes the histogram look a little nicer and not that cut off
    bins = [res * x - (res / 2) for x in range(-bin_half_count, bin_half_count + 2)]

    compressed = numpy.ma.array(data).compressed()
    n, bins, patches = subplot.hist(compressed, bins=bins, alpha=0.7)

    bincenters = 0.5 * (bins[1:] + bins[:-1])
    y = matplotlib.mlab.normpdf(bincenters, mu, sigma) * len(compressed) * res
    subplot.plot(bincenters, y, 'r--')

    common_plot_settings(subplot,
        min_x = mu - threshold,
        max_x = mu + threshold,
        min_y = 0,
        max_y = numpy.max(n))

    return mu, sigma, outliers
