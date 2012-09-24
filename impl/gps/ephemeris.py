class Ephemeris(object):
    def __init__(self):
        self._current_week = None

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

