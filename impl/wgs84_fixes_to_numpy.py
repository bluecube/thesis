#!/usr/bin/python
"""
wgs84_fixes_to_numpy.py

Extract latitude, longitude and hdop from the recording.
"""

from __future__ import division
import logging
import gps
import numpy

def fixes_to_numpy(gps_filename):
    """ The main fixes generator. """
    logging.info("Retrieving fixes")
    source = gps.open_gps(gps_filename)
    return numpy.fromiter(
        (
            (msg.latitude, msg.longitude, msg.hdop)
            for msg in source.filtered_messages([gps.sirf_messages.GeodeticNavigationData])
        ),
        dtype=[('lat', numpy.float), ('lon', numpy.float), ('hdop', numpy.float)])

def open_source(source_filename):
    """ Wrapper for opening recordings or preprocessed arrays transparently."""
    try:
        return numpy.load(source_filename)
    except IOError:
        return fixes_to_numpy(source_filename)

if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level = logging.INFO
    )

    arg_parser = argparse.ArgumentParser(
        description="Turn GPS fixes to a numpy array for faster procesing.")
    arg_parser.add_argument('source',
        help="A recording of SiRF messages.")
    arg_parser.add_argument('target',
        help="Target Numpy binary array file (*.npy, typically).", type=argparse.FileType('wb'))
    arguments = arg_parser.parse_args()

    fixes = fixes_to_numpy(arguments.source)

    logging.info("Saving")
    numpy.save(arguments.target, fixes)
