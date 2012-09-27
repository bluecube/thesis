import collections

StationState = collections.namedtuple('StationState', [
    'pos',
    'velocity',
    'clock_offset',
    'clock_drift'])

class Ephemeris(object):
    def __init__(self):
        self._current_week = None

    def sv_state(self, prn, week, time):
        return StationState(
            pos = self.sv_pos(prn, week, time),
            velocity = self.sv_velocity(prn, week, time),
            clock_offset = self.sv_clock_offset(prn, week, time),
            clock_drift = self.sv_clock_drift(prn, week, time))

    def sv_pos(self, prn, week, time):
        """Return numpy matrix with SV position."""
        raise NotImplementedError()

    def sv_clock_offset(self, prn, week, time):
        """Return SV clock offset."""
        raise NotImplementedError()

    def sv_velocity(self, prn, week, time):
        """Return numpy matrix with SV velocity."""
        raise NotImplementedError()

    def sv_clock_drift(self, prn, week, time):
        """Return SV clock drift."""
        raise NotImplementedError()

    def sv_pos_current_week(self, prn, time):
        """Return numpy matrix with SV position.
        This version uses the current week."""
        return self.sv_pos(prn, self._current_week, time)

    def sv_clock_offset_current_week(self, prn, time):
        """Return SV clock offset.
        This version uses the current week."""
        return self.sv_clock_offset(prn, self._current_week, time)

    def sv_velocity_current_week(self, prn, time):
        """Return numpy matrix with SV velocity.
        This version uses the current week."""
        return self.sv_velocity(prn, self._current_week, time)

    def sv_clock_drift_current_week(self, prn, time):
        """Return SV clock drift.
        This version uses the current week."""
        return self.sv_clock_drift(prn, self._current_week, time)

    def sv_state_current_week(self, prn, time):
        return StationState(
            pos = self.sv_pos(prn, self._current_week, time),
            velocity = self.sv_velocity(prn, self._current_week, time),
            clock_offset = self.sv_clock_offset(prn, self._current_week, time),
            clock_drift = self.sv_clock_drift(prn, self._current_week, time))

    def sv_time_to_sys_time(self, prn, sv_time):
        """Convert between time frames on the satellite and the system time
        based on the clock SV clock offset.
        This is used mainly for transmission times.

        This means finding roots of
        sys_time + sv_clock_offset(sys_time) - sv_time = 0
        Easy peasy."""
        raise NotImplementedError()
