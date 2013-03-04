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
                measurement.satellite_id) # TODO: Clean up
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

    def _tropo_delay(self):
        """ Tropospheric delay from hopfield model, based on default meteorologic parameters
        and saved receiver and SV position.

        http://home.tiscali.nl/~samsvl/pseucorr.htm
        """

        sq_el = self._sv_elevation_squared
        return 2.312 / math.sin(math.sqrt(sq_el + 1.904E-3)) + 0.084 / math.sin(math.sqrt(sq_el + 0.6854E-3))

        # """ Tropospheric delay from hopfield model, based on the meteorologic parameters
        # and saved receiver and SV position.

        # t_amb -- ambient temperature in degrees Celsius
        # p_amb -- ambient pressure in kPa
        # p_vap -- ambient vapour pressure in kPa"""

        # # iverse of ambient temperature in kelvins.
        # inv_t_amb = 1 / (t_amb + 273.15)

        # # Dry and we air refractivity at sea level
        # n_d = 776.24 * p_amb * inv_t_amb
        # n_w = -129.2 * p_vap * inv_t_amb + 3719000 * p_vap * inv_t_amb * inv_t_amb

        # # upper extent of dry and wet atmosphere from sea level
        # h_d = 113850 * p_amb / n_d
        # h_w = 113850 * (1255 * inv_t_amb + 0.05) * p_vap / n_w

        # zenith_tropo_delay = 0.2e-6 * (n_d * h_d + n_w * h_w)




    def pseudorange_error(self):
        """Return difference between geometric range (determined from ephemeris and
        receiver state) and somehow corrected pseudorange."""
        # First we correct for receiver and satellite clock offsets
        corrected_pseudorange = (
            self._measurement.pseudorange -
            C * (self._receiver_state.clock_offset - self._sv_state.clock_offset))

        corrected_pseudorange += self._correction
        corrected_pseudorange -= self._tropo_delay()

        error = corrected_pseudorange - self._geom_range

        #if abs(error) > 10000000:
        #    print(error)
        #    print(corrected_pseudorange)
        #    print(self._receiver_state)
        #    print(self._sv_state)
        #    print(self._measurement)
        
        return error

    def doppler_error(self):
        raise NotImplementedError()
