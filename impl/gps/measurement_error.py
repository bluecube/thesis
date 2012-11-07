from __future__ import division, print_function
import numpy

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

        transmission_time_sys = self._ephemeris.sv_time_to_sys_time(
            measurement.satellite_id,
            time_of_transmission_sv)

        sv_state = self._ephemeris.sv_state_current_week(
            measurement.satellite_id,
            transmission_time_sys)

        self._transmission_time_sys = transmission_time_sys
        self._sv_state = sv_state
        self._measurement = measurement

        return True

    def _set_receiver_pos(self, receiver_position):
        self._user_to_sv = self._sv_state.pos - receiver_position
        self._geom_range = numpy.linalg.norm(self._user_to_sv)

    def receiver_clock_offset(self, measurement, receiver_position):
        """Returns clock offset receiver would have if pseudorange_error was 0.
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

    def pseudorange_error(self):
        """Return difference between geometric range (determined from ephemeris and
        receiver state) and somehow corrected pseudorange."""
        # First we correct for receiver and satellite clock offsets
        corrected_pseudorange = (
            self._measurement.pseudorange -
            C * (self._receiver_state.clock_offset - self._sv_state.clock_offset))

        error = corrected_pseudorange - self._geom_range

        #if abs(error) > 10000000:
        #    print(error)
        #    print(corrected_pseudorange)
        #    print(self._receiver_state)
        #    print(self._sv_state)
        #    print(self._measurement)
        
        return error

    @property
    def doppler_error(self):
        raise NotImplementedError()
