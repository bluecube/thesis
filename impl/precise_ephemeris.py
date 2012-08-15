#!/usr/bin/python

import math
import logging
import argparse
import gps
import pyproj
import numpy
import matplotlib.pyplot as plt


def sv_tuples_generator(source):
    """
    Yields tuples, one for every sv state message,
    containing pos_x, pos_y, pos_z, clock_bias,
        extended_gps_week, gps_time, satellite_id.
    """
    for block in source.split_to_cycles(
        [gps.sirf_messages.NavigationLibrarySVStateData, gps.sirf_messages.ClockStatusData]):
        for msg in block:
            if isinstance(msg, gps.sirf_messages.ClockStatusData):
                week = msg.extended_gps_week

        for msg in block:
            if not isinstance(msg, gps.sirf_messages.NavigationLibrarySVStateData):
                continue
            yield (msg.pos_x, msg.pos_y, msg.pos_z, msg.clock_bias,
                week, msg.gps_time, msg.satellite_id)

logging.basicConfig(
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level = logging.INFO
)

arg_parser = argparse.ArgumentParser(
    description="Calculate difference of precide ephemeris and\n"
    "transmitted orbits.")
arg_parser.add_argument('gps')
arg_parser.add_argument('--hist-resolution', default=0.5, type=float,
    help="Width of the histogram bin.")
arguments = arg_parser.parse_args()

source = gps.open_gps(arguments.gps)
ephemeris = gps.precise_ephemeris.IGSEphemeris('ftp://igs.ensg.ign.fr/pub/igs/products/')

logging.info("Reading broadcast ephemeris")
broadcast = numpy.fromiter(
    sv_tuples_generator(source),
    dtype=[('x', numpy.float), ('y', numpy.float), ('z', numpy.float),
    ('clock_offset', numpy.float), ('week', numpy.int16), ('time', numpy.float), ('sv_id', numpy.float)])
logging.info("Done")

logging.info("Reading precise ephemeris")
precise = numpy.fromiter(
    (
        (ephemeris.sv_pos_x(x['sv_id'], x['week'], x['time']),
        ephemeris.sv_pos_y(x['sv_id'], x['week'], x['time']),
        ephemeris.sv_pos_z(x['sv_id'], x['week'], x['time']),
        ephemeris.sv_clock_offset(x['sv_id'], x['week'], x['time']))
        for x in broadcast
    ),
    dtype=[('x', numpy.float), ('y', numpy.float), ('z', numpy.float),
    ('clock_offset', numpy.float)])
logging.info("Done")

week = 1623
x = numpy.arange(1, 12*3600)
y =  numpy.fromiter(
    (ephemeris.sv_pos_x(1, x['week'], x['time']),
        ephemeris.sv_pos_y(x['sv_id'], x['week'], x['time']),
        ephemeris.sv_pos_z(x['sv_id'], x['week'], x['time']),
        ephemeris.sv_clock_offset(x['sv_id'], x['week'], x['time']))
        for x in broadcast
    ),
    dtype=[('x', numpy.float), ('y', numpy.float), ('z', numpy.float),
    ('clock_offset', numpy.float)])

    
    differences_plot.plot(broadcast['time'], difference[what], label=what)

logging.info("Calculating differences")
difference = {}
for what in ['x', 'y', 'z', 'clock_offset']:
    difference[what] = broadcast[what] - precise[what]
logging.info("Done")

print("Count: {}".format(len(difference['x'])))
print("Max abs difference: X: {} m; Y: {} m; Z: {} m; clock: {} s".format(
    *[numpy.max(numpy.abs(difference[what])) for what in ['x', 'y', 'z', 'clock_offset']]))

fig1 = plt.figure()
differences_plot = fig1.add_subplot(1, 1, 1)

for what in ['x', 'y', 'z', 'clock_offset']:
    differences_plot.plot(broadcast['time'], difference[what], label=what)

differences_plot.set_title('Coordinate differences')
differences_plot.set_xlabel('GPS System time [s]')
differences_plot.set_ylabel('Difference [m]')

plt.show()

