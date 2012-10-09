#!/usr/bin/python

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
import mpl_toolkits.mplot3d

logging.basicConfig(
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level = logging.INFO
)

arg_parser = argparse.ArgumentParser(
    description="Calculate WGS84 errors.\n"
    "Assumes that the receiver was stationary during whole recording.")
arg_parser.add_argument('source',
    help="A recording of SiRF messages or saved numpy array (*.npy).")
arg_parser.add_argument('--plotted-sample-count', default=5000, type=int,
    help="Number of samples that will be plotted in the scatter plots.")
arg_parser.add_argument('--save-hdop-plot', default=None, type=str,
    help="Where to save the HDOP plot.")
arg_parser.add_argument('--save-fixes-plot', default=None, type=str,
    help="Where to save the fixes plot.")
arg_parser.add_argument('--no-show', action='store_true',
    help="Don't show the plots, only save them.")
arg_parser.add_argument('--max-plot-hdop', type=float,
    help="Don't plot hdops larger than this.")
arg_parser.add_argument('--max-plot-error', type=float,
    help="Don't plot hdop errors larger than this.")
arguments = arg_parser.parse_args()

fixes = wgs84_fixes_to_numpy.open_source(arguments.source)

hdop = fixes['hdop']
logging.info("Done. Have %i fixes", len(fixes))

logging.info("Projecting")
proj = pyproj.Proj(proj='ortho', ellps='WGS84',
    lat_0 = numpy.mean(fixes['lat']),
    lon_0 = numpy.mean(fixes['lon']))
(x, y) = proj(fixes['lon'], fixes['lat'])
logging.info("Done")

logging.info("Calculating distances")
dist_squared = x**2 + y**2
dist = numpy.sqrt(dist_squared)
logging.info("Done")

logging.info("HDOP statistics")
used_hdop = numpy.unique(hdop)
hdop_drms = numpy.empty_like(used_hdop)
hdop_weight = numpy.empty_like(used_hdop)

for i, current_hdop in enumerate(used_hdop):
    mask = (hdop != current_hdop)

    masked_dist_squared = numpy.ma.array(dist_squared, mask = mask)
    hdop_drms[i] = numpy.ma.mean(masked_dist_squared)
    hdop_weight[i] = numpy.ma.count(masked_dist_squared)

hdop_drms = numpy.sqrt(hdop_drms)

def goal_func(params):
    ret = hdop_drms - numpy.sqrt((params[0] * used_hdop)**2 + params[1]**2)
    return ret * numpy.sqrt(hdop_weight)

hdop_drms_nonlinear, _ = scipy.optimize.leastsq(goal_func, (1, 1))
hdop_drms_linear = numpy.sum(used_hdop * hdop_drms * hdop_weight) / numpy.sum(used_hdop * used_hdop * hdop_weight)
print("Fitted linear model: {} * HDOP".format(hdop_drms_linear))
print("Fitted non linear model: sqrt(({} * HDOP)**2 + {}**2)".format(*hdop_drms_nonlinear))

logging.info("Done")

plot_step = (len(fixes) // arguments.plotted_sample_count) or 1
print("Scatter plots will only use 1/{} samples".format(plot_step))

fig1 = plt.figure()
fixes_plot = fig1.add_subplot(1, 1, 1)
fixes_plot.scatter(x, y, c=hdop, marker='.', s=40, alpha=0.5, edgecolors='none', rasterized=True)
fixes_plot.set_xlabel('Easting [m]')
fixes_plot.set_ylabel('Northing [m]')
fixes_plot.set_aspect(1)
fixes_plot.autoscale(tight=True)

matplotlib_settings.common_plot_settings(fixes_plot, set_limits=False)

fig2 = plt.figure()
if arguments.max_plot_hdop is not None:
    max_plot_hdop = arguments.max_plot_hdop
else:
    max_plot_hdop = numpy.max(hdop)

if arguments.max_plot_error is not None:
    max_plot_error = arguments.max_plot_error
else:
    max_plot_error = numpy.max(dist)

hdop_plot = fig2.add_subplot(1, 1, 1)
hdop_plot.scatter(hdop[::plot_step], dist[::plot_step], marker='.',
    s=40, alpha=0.5, edgecolors='none', label="Measured data", rasterized=True)
hdop_plot.scatter(used_hdop, hdop_drms, c='y', label="DRMS")

x = numpy.linspace(0, numpy.max(used_hdop), num = 200)
hdop_plot.plot(x, hdop_drms_linear * x, c='g', label="Fitted linear model")
hdop_plot.plot(x, numpy.sqrt((hdop_drms_nonlinear[0] * x)**2 + hdop_drms_nonlinear[1]**2), c='r', label="Fitted non-linear model")
hdop_plot.set_xlabel('HDOP')
hdop_plot.set_ylabel('Error [m]')
hdop_plot.legend().get_frame().set_alpha(0.75)

matplotlib_settings.common_plot_settings(hdop_plot,
    0, max_plot_hdop,
    0, max_plot_error)

count_inside = sum((hdop <= max_plot_hdop) & (dist <= max_plot_error))
print("{:.2%} is in the area {}x{}".format(count_inside / len(dist), max_plot_hdop, max_plot_error))

if arguments.save_hdop_plot is not None:
    fig2.savefig(arguments.save_hdop_plot)
    logging.info("Saved %s", arguments.save_hdop_plot)

if not arguments.no_show:
    plt.show()

