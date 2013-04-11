from __future__ import division, print_function
import numpy
import math

C = 299792458 # Speed of light

class MeasurementError:
    """Calculate position and velocity errors based on ephemeris, receiver state and
    a GPS measurement."""

    def __init__(self, ephemeris):
        self._ephemeris = ephemeris

    def set_measurement(self, measurement):
        """ Set the measurement for the error calculation
        Returns True if measurement is valid, False otherwise."""

        if measurement.pseudorange == 0:
            return False

        time_of_transmission_sv = (
            measurement.gps_sw_time - measurement.pseudorange / C)

        try:
            transmission_time_sys = self._ephemeris.sv_time_to_sys_time(
                measurement.satellite_id,
                time_of_transmission_sv)

            sv_state = self._ephemeris.sv_state_current_week(
                measurement.satellite_id,
                transmission_time_sys)

            self._correction = self._ephemeris.correction(
                measurement.satellite_id)
        except LookupError:
            return False

        self._transmission_time_sys = transmission_time_sys
        self._sv_state = sv_state
        self._measurement = measurement

        return True

    def _set_receiver_pos(self, receiver_position):
        self._user_to_sv = self._sv_state.pos - receiver_position
        self._geom_range = math.sqrt(math.fsum(x*x for x in self._user_to_sv.flat))

        up = receiver_position
        user_to_sv = self._user_to_sv

        tmp = math.fsum(x*y for x, y in zip(up.flat, user_to_sv.flat))
        self._sv_elevation_squared = tmp * tmp / (
            math.fsum(x*x for x in up.flat) * math.fsum(x*x for x in user_to_sv.flat))

    def receiver_clock_offset(self, measurement, receiver_position):
        """Returns clock offset receiver would have if pseudorange_error was 0.
        This is equal to pseudorange_error if receiver_clock_offset == 0, the divided by C
        Internally calls set_measurement.
        If the measurement is not valid, this method returns None."""
        if not self.set_measurement(measurement):
            return None
        self._set_receiver_pos(receiver_position)

        return (self._measurement.pseudorange - self._geom_range) / C + self._sv_state.clock_offset

    def set_receiver_state(self, receiver_state):
        """ Set the receiver state. Must be called after set_measurement """

        self._receiver_state = receiver_state
        self._set_receiver_pos(receiver_state.pos)

        velocity_diff = self._sv_state.velocity - receiver_state.velocity
        self._relative_velocity = \
            math.fsum(x*y for x, y in zip(velocity_diff.flat, self._user_to_sv.flat)) / \
            self._geom_range

    def _tropo_delay(self):
        """ Tropospheric delay from hopfield model, based on default meteorologic parameters
        and saved receiver and SV position.

        http://home.tiscali.nl/~samsvl/pseucorr.htm
        """

        sq_el = self._sv_elevation_squared
        return 2.312 / math.sin(math.sqrt(sq_el + 1.904E-3)) + 0.084 / math.sin(math.sqrt(sq_el + 0.6854E-3))


    def pseudorange_error(self):
        """Return difference between geometric range (determined from ephemeris and
        receiver state) and somehow corrected pseudorange."""
        # First we correct for receiver and satellite clock offsets
        corrected_pseudorange = (
            self._measurement.pseudorange -
            C * (self._receiver_state.clock_offset - self._sv_state.clock_offset))

        corrected_pseudorange += self._tropo_delay()
        error = corrected_pseudorange - self._geom_range
        return error

    def doppler_error(self):
        corrected_reported_velocity = (
            self._measurement.carrier_freq -
            C * (self._receiver_state.clock_drift))
        return corrected_reported_velocity - self._relative_velocity
