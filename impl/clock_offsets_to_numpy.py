#!/usr/bin/python
from __future__ import division, print_function

import argparse
import numpy
import logging
import resource
import itertools

import gps
import util

logging.basicConfig(
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level = logging.INFO
)

CLOCK_CORRECTION_THRESHOLD = 1e6 # Distance jump in meters that is considered as clock correction.

class _Worker:
    def cycle_end_callback(self):
        count = 0
        error_sum = 0

        cycle_start = len(self.measurement_errors)

        if len(self.measurements.collected) == 0:
            return

        if self.measurements.collected[0].gps_sw_time < self.unmodified_last_time:
            self.week_offset += 7 * 24 * 3600

        for measurement in self.measurements.collected:
            me = gps.MeasurementError(self.ephemeris)
            if not me.set_measurement(measurement):
                continue
            me.set_receiver_state(self.receiver_state)

            error = me.pseudorange_error()

            count += 1
            error_sum += error
            self.times.append(measurement.gps_sw_time + self.week_offset)
            self.unmodified_last_time = measurement.gps_sw_time
            self.sv_ids.append(measurement.satellite_id)
            self.measurement_errors.append(error)

        self.measurements.clear()

        if not count:
            return

        avg_error = error_sum / count

        if self.last_avg_error is None:
            # This is the first record
            current_clock_correction = 0
        else:
            time_diff = self.times[-1] - self.last_time
            assert time_diff > 0

            error_diff = avg_error - self.last_avg_error
            derivation = error_diff / time_diff # unit: meter / receiver_second

            #sys_time_diff = time_diff - (clock_offset(self.times[-1]) - clock_offset(self.last_time))
            #new_sys_derivation = error_diff / sys_time_diff # unit: meter / second

            if abs(derivation) > CLOCK_CORRECTION_THRESHOLD:
                # This is clock correction

                self.clock_corrections.append(cycle_start)

                correction_magnitude = error_diff - self.last_derivation * time_diff
                current_clock_correction = self.clock_correction_values[-1] - correction_magnitude
            else:
                current_clock_correction = self.clock_correction_values[-1]
                self.last_derivation = derivation

        self.clock_correction_values.extend(count * [current_clock_correction])
        self.last_avg_error = avg_error
        self.last_time = self.times[-1]

    def fit_clock_offsets(self, x, y, width):
        drifts, offsets = util.windowed_least_squares(x, y, width)

        del drifts
        mask = numpy.abs(y - offsets) < arguments.outlier_threshold
        del offsets

        return util.windowed_least_squares(x, y, width, mask)

    def do(self, source_filename, receiver_pos, fit_window, outlier_threshold):
        source = gps.open_gps(source_filename)
        self.receiver_state = gps.StationState(
            pos = receiver_pos,
            velocity = numpy.matrix([[0, 0, 0]]),
            clock_offset = 0,
            clock_drift = 0)

        self.ephemeris = gps.BroadcastEphemeris()
        self.measurements = gps.MessageCollector(gps.sirf_messages.NavigationLibraryMeasurementData)

        self.clock_corrections = []

        self.times = [] # Measurement times in receiver time frame
        self.sv_ids = []
        self.measurement_errors = []
        self.clock_correction_values  = []

        self.last_avg_error = None

        self.last_derivation = None
        self.last_time = None
        self.unmodified_last_time = None
        self.week_offset = 0 # offset of the current gps week from the first recorded one

        logging.info("Reading measurements...")

        try:
            source.loop([self.ephemeris, self.measurements], self.cycle_end_callback)
        except KeyboardInterrupt:
            pass

        self.cycle_end_callback() # Last cycle doesn't end, so this wouldn't be otherwise called.

        logging.info("Processing...")

        logging.info("- Convert to arrays...")
        self.times = numpy.array(self.times, dtype=numpy.float)
        self.sv_ids = numpy.array(self.sv_ids, dtype=numpy.float)
        self.measurement_errors = numpy.array(self.measurement_errors, dtype=numpy.float)
        self.clock_correction_values = numpy.array(self.clock_correction_values, dtype=numpy.float)

        logging.info("- Fit clock offset...")

        clock_drifts, clock_offsets = self.fit_clock_offsets(self.times,
            self.measurement_errors + self.clock_correction_values,
            fit_window)
        clock_offsets -= self.clock_correction_values

        del self.clock_correction_values

        return numpy.fromiter(
            itertools.izip(
                self.times,
                self.sv_ids,
                self.measurement_errors,
                clock_offsets,
                clock_drifts
                ),
            dtype=[
                ('times', numpy.float),
                ('sv_ids', numpy.float),
                ('errors', numpy.float),
                ('clock_offsets', numpy.float),
                ('clock_drifts', numpy.float)])

def open_source(source_filename, receiver_pos, fit_window, outlier_threshold):
    try:
        return numpy.load(source_filename)
    except IOError:
        pass

    w = _Worker()
    return w.do(source_filename, receiver_pos, fit_window, outlier_threshold)

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description="Extract pseudoranges and baseline clock offsets from the recording. "
        "Assumes that the receiver was stationary during whole recording.")
    arg_parser.add_argument('gps', help="GPS receiver or recording.")
    arg_parser.add_argument('target',
        help="Target Numpy binary array file (*.npy, typically).",
        type=argparse.FileType('wb'))
    arg_parser.add_argument('--receiver-pos', type=numpy.matrix, default=None, required=True,
        help="Ground truth receiver position.")
    arg_parser.add_argument('--fit-window', type=float, default=2 * 60,
        help="Controls how large the window for smoothing clock offsets will be, in seconds.")
    arg_parser.add_argument('--outlier-threshold', action='store', type=float, default=250,
        help="Distance in meters from the smoothed pseudorange at which the point is considered an outlier")
    arguments = arg_parser.parse_args()

    w = _Worker()
    ret = w.do(arguments.gps, arguments.receiver_pos, arguments.fit_window, arguments.outlier_threshold)

    logging.info("Saving")
    numpy.save(arguments.target, ret)
