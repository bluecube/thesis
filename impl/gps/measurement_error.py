from __future__ import division, print_function
import numpy

C = 299792458 # Speed of light

class MeasurementError:
    """Calculate position and velocity errors based on ephemeris, receiver state and
    a GPS measurement."""

    def __init__(self, ephemeris):
        self._ephemeris = ephemeris

    def set_params(self, receiver_state, measurement):
        """Input the other two sets of parameters necessary for the
        calulation and precompute the common stuff.

        receiver_state is a StationState named tuple,
        measurement is simply the SiRF message."""

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
        self._receiver_state = receiver_state
        self._measurement = measurement
        self._user_to_sv = sv_state.pos - receiver_state.pos

    @property
    def receiver_clock_offset(self):
        """In this context receiver clock offset is the clock offset receiver would
        have if pseudorange_error was 0.
        This ignores receiver clock offset field in the receiver state (obviously)."""
        
        geom_range = numpy.linalg.norm(self._user_to_sv)

        return (self._measurement.pseudorange - geom_range) / C + self._sv_state.clock_offset

    @property
    def pseudorange_error(self):
        """Return difference between geometric range (determined from ephemeris and
        receiver state) and somehow corrected pseudorange."""
        # First we correct for receiver and satellite clock offsets
        corrected_pseudorange = (
            self._measurement.pseudorange -
            C * (self._receiver_state.clock_offset - self._sv_state.clock_offset))

        geom_range = numpy.linalg.norm(self._user_to_sv)

        return corrected_pseudorange - geom_range

    @property
    def doppler_error(self):
        raise NotImplementedError()
