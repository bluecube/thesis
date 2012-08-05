#!/usr/bin/python

from __future__ import division

import matplotlib_settings

import math
import logging
import argparse
import gps
import pyproj
import numpy
import matplotlib.pyplot as plt
import mpl_toolkits.mplot3d

logging.basicConfig(
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level = logging.INFO
)

arg_parser = argparse.ArgumentParser(
    description="Calculate WGS84 errors.\n"
    "Assumes that the receiver was stationary during whole recording.")
arg_parser.add_argument('gps',
    help="A recording of SiRF messages.")
arg_parser.add_argument('--polynomial-degree', default=4, type=int,
    help="Degree of interpolation polynomial.")
arg_parser.add_argument('--hist-resolution', default=0.5, type=float,
    help="Width of the histogram bin.")
arg_parser.add_argument('--plotted-sample-count', default=5000, type=int,
    help="Number of samples that will be plotted in the scatter plots.")
arg_parser.add_argument('--save-hdop-plot', default=None, type=str,
    help="Where to save the HDOP plot.")
arg_parser.add_argument('--save-fixes-plot', default=None, type=str,
    help="Where to save the fixes plot.")
arg_parser.add_argument('--save-hist-plot', default=None, type=str,
    help="Where to save the histogram plot.")
arg_parser.add_argument('--no-show', action='store_true',
    help="Don't show the plots, only save them.")
arg_parser.add_argument('--max-plot-hdop', type=float,
    help="Don't plot hdops larger than this.")
arg_parser.add_argument('--max-plot-error', type=float,
    help="Don't plot hdop errors larger than this.")
arguments = arg_parser.parse_args()

source = gps.open_gps(arguments.gps)

logging.info("Retrieving fixes")
fixes = numpy.fromiter(
    (
        (msg.latitude, msg.longitude, msg.hdop)
        for msg in source.filtered_messages([gps.sirf_messages.GeodeticNavigationData])
    ),
    dtype=[('lat', numpy.float), ('lon', numpy.float), ('hdop', numpy.float)])
hdop = fixes['hdop']
logging.info("Done. Have %i fixes", len(fixes))

logging.info("Projecting")
proj = pyproj.Proj(proj='ortho', ellps='WGS84',
    lat_0 = numpy.mean(fixes['lat']),
    lon_0 = numpy.mean(fixes['lon']))
(x, y) = proj(fixes['lon'], fixes['lat'])
logging.info("Done")

logging.info("Calculating distances")
dist = numpy.hypot(x, y)
logging.info("Done")

logging.info("HDOP statistics")
used_hdop = numpy.unique(hdop)
hdop_mean_error = numpy.empty_like(used_hdop)

for i, current_hdop in enumerate(used_hdop):
    masked_dist = numpy.ma.array(dist, mask = (hdop != current_hdop))
    hdop_mean_error[i] = numpy.ma.mean(masked_dist)

hist, error_bins, hdop_bins = numpy.histogram2d(
    dist, hdop,
    (
        (numpy.max(dist) - numpy.min(dist)) / arguments.hist_resolution,
        (numpy.max(hdop) - numpy.min(hdop)) / 0.2
    )
    )

hdop_error_poly = numpy.polynomial.polynomial.Polynomial.fit(hdop, dist, deg=arguments.polynomial_degree)
hdop_error_linear = numpy.sum(hdop * dist) / numpy.sum(hdop*hdop)
print("Fitted polynomial: {}".format(hdop_error_poly))
print("Fitted Error(HDOP = 1): {}".format(hdop_error_linear))

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

fig2 = plt.figure()
if 'max_plot_hdop' in arguments:
    max_plot_hdop = arguments.max_plot_hdop
else:
    max_plot_hdop = numpy.max(hdop)

if 'max_plot_error' in arguments:
    max_plot_error = arguments.max_plot_error
else:
    max_plot_error = numpy.max(dist)

hdop_plot = fig2.add_subplot(1, 1, 1)
hdop_plot.scatter(hdop[::plot_step], dist[::plot_step], marker='.',
    s=40, alpha=0.5, edgecolors='none', label="Measured data", rasterized=True)
hdop_plot.scatter(used_hdop, hdop_mean_error, c='y', label="Mean error for HDOP")

x = numpy.linspace(0, numpy.max(used_hdop))
hdop_plot.plot(x, hdop_error_poly(x), c='r', label="Fitted polynomial")
hdop_plot.plot(x, hdop_error_linear * x, c='g', label="Fitted linear model")
hdop_plot.set_xlabel('HDOP')
hdop_plot.set_ylabel('Error [m]')
hdop_plot.legend().get_frame().set_alpha(0.75)

xmargin, ymargin = hdop_plot.margins()
margin = max_plot_hdop * xmargin
hdop_plot.set_xlim([- margin, max_plot_hdop + margin])
margin = max_plot_error * xmargin
hdop_plot.set_ylim([- margin, max_plot_error + margin])

count_inside = sum((hdop <= max_plot_hdop) & (dist <= max_plot_error))
print("{:.2%} % is in the area {}x{}".format(count_inside / len(dist), max_plot_hdop, max_plot_error))

if arguments.save_hdop_plot is not None:
    fig2.savefig(arguments.save_hdop_plot)
    logging.info("Saved %s", arguments.save_hdop_plot)

#fig3 = plt.figure()
#hist_plot = fig3.add_subplot(1, 1, 1, projection='3d')
#
#max_hdop = numpy.max(hdop)
#for i, current_hdop in enumerate(hdop_bins[:-1]):
#    c = 'red' if i % 2 else 'blue'
#    hist_plot.bar(error_bins[:-1], hist[:,i], current_hdop, zdir='y', color = c, 
#        width = arguments.hist_resolution, alpha=0.75)
#
#hist_plot.set_xlabel('Error [m]')
#hist_plot.set_ylabel('HDOP')
#hist_plot.set_zlabel('Count')

if not arguments.no_show:
    plt.show()

