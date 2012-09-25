#!/usr/bin/python

import math
import logging
import argparse
import gps
import gps.sirf_messages
import gps.message_observer_decorator

import pyproj
import numpy
import matplotlib.pyplot as plt

@gps.message_observer_decorator(gps.sirf_messages.NavigationLibrarySVStateData)
def immediately(message):
    """Compare the SV positions in the time for which the interpolation is calculated
    by sirf."""

    precise_ephemeris_pos = precise_ephemeris.sv_pos_current_week(
        message.satellite_id,
        message.gps_time)

    pos_errors.append(precise_ephemeris_pos - message.pos)


@gps.message_observer_decorator(gps.sirf_messages.NavigationLibraryMeasurementData)
def on_use(message):
    """Compare the SV positions in the time when pseudorange is transmitted"""
    pass

logging.basicConfig(
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level = logging.INFO
)

arg_parser = argparse.ArgumentParser(
    description="Calculate difference of precise ephemeris and\n"
    "broadcast orbits.")
arg_parser.add_argument('gps')
arg_parser.add_argument('--hist-resolution', default=0.5, type=float,
    help="Width of the histogram bin.")
arguments = arg_parser.parse_args()

source = gps.open_gps(arguments.gps)
broadcast_ephemeris = gps.BroadcastEphemeris()
precise_ephemeris = gps.IGSEphemeris('ftp://igs.ensg.ign.fr/pub/igs/products/')


pos_errors = []
interpolation_distance = []


try:
    source.loop([
        broadcast_ephemeris,
        precise_ephemeris,
        immediately,
        #on_use
        ])
except KeyboardInterrupt:
    pass

pos_errors = numpy.array(pos_errors)
print(pos_errors)


print numpy.amax(pos_errors)
#
#
#
#x = numpy.arange(1, 12*3600)
#y =  numpy.fromiter(
#    (ephemeris.sv_pos_x(1, x['week'], x['time']),
#        ephemeris.sv_pos_y(x['sv_id'], x['week'], x['time']),
#        ephemeris.sv_pos_z(x['sv_id'], x['week'], x['time']),
#        ephemeris.sv_clock_offset(x['sv_id'], x['week'], x['time']))
#        for x in broadcast
#    ),
#    dtype=[('x', numpy.float), ('y', numpy.float), ('z', numpy.float),
#    ('clock_offset', numpy.float)])
#
#    
#    differences_plot.plot(broadcast['time'], difference[what], label=what)
#
#logging.info("Calculating differences")
#difference = {}
#for what in ['x', 'y', 'z', 'clock_offset']:
#    difference[what] = broadcast[what] - precise[what]
#logging.info("Done")
#
#print("Count: {}".format(len(difference['x'])))
#print("Max abs difference: X: {} m; Y: {} m; Z: {} m; clock: {} s".format(
#    *[numpy.max(numpy.abs(difference[what])) for what in ['x', 'y', 'z', 'clock_offset']]))
#
#fig1 = plt.figure()
#differences_plot = fig1.add_subplot(1, 1, 1)
#
#for what in ['x', 'y', 'z', 'clock_offset']:
#    differences_plot.plot(broadcast['time'], difference[what], label=what)
#
#differences_plot.set_title('Coordinate differences')
#differences_plot.set_xlabel('GPS System time [s]')
#differences_plot.set_ylabel('Difference [m]')
#
#plt.show()
#
