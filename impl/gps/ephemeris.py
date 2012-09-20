class Ephemeris(object):
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

