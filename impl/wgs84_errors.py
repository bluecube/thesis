#!/usr/bin/python

import math
import logging
import argparse
import gps
import pyproj
import numpy
import matplotlib.pyplot as plt

logging.basicConfig(
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level = logging.INFO
)

arg_parser = argparse.ArgumentParser(
    description="Calculate the UERE from recorded data.\n"
    "Assumes that the receiver was stationary during whole recording.")
arg_parser.add_argument('gps')
arg_parser.add_argument('--hist-resolution', default=0.1, type=float,
    help="Width of the histogram bin.")
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
hdop_rms = numpy.empty_like(used_hdop)

for i, current_hdop in enumerate(used_hdop):
    masked_dist = numpy.ma.array(dist, mask = (hdop == current_hdop))
    hdop_rms[i] = math.sqrt(numpy.mean(masked_dist * masked_dist))

logging.info("Done")


fig1 = plt.figure()
fixes_plot = fig1.add_subplot(1, 1, 1)
fixes_plot.scatter(x, y, c=hdop, marker='.', s=40, alpha=0.75, edgecolors='none')
fixes_plot.set_title('Fixes')
fixes_plot.set_xlabel('Easting [m]')
fixes_plot.set_ylabel('Northing [m]')
fixes_plot.set_aspect(1)

fig2 = plt.figure()
hdop_plot = fig2.add_subplot(1, 1, 1)
hdop_plot.scatter(used_hdop, hdop_rms)
hdop_plot.set_xlabel('HDOP [m]')
hdop_plot.set_ylabel('Error RMS [m]')


plt.show()

