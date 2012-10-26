from . import ephemeris
from . import message_observer
from . import sirf_messages

class BroadcastEphemeris(ephemeris.Ephemeris, message_observer.MessageObserver):
    """
    Ephemeris extracted from received SiRF messages.
    Only uses the last SV state message from the message stream,
    this means that the satellite path is approximated by linear one
    around the time that the receiver decides.
    Completely ignores the GPS week field.
    """
    def __init__(self):
        ephemeris.Ephemeris.__init__(self)
        self._sv_states = {}

    def sv_pos(self, prn, week, time):
        """Return numpy matrix with SV position."""
        state = self._sv_states[prn]
        return state.pos + (time - state.gps_time) * state.v

    def sv_clock_offset(self, prn, week, time):
        """Return SV clock offset."""
        state = self._sv_states[prn]
        return state.clock_bias + (time - state.gps_time) * state.clock_drift

    def sv_velocity(self, prn, week, time):
        """Return numpy matrix with SV velocity."""
        return self._sv_states[prn].v

    def sv_clock_drift(self, prn, week, time):
        """Return SV clock drift."""
        return self._sv_states[prn].clock_drift

    def sv_time_to_sys_time(self, prn, sv_time):
        state = self._sv_states[prn]
        return (
            (sv_time - state.clock_bias + state.gps_time * state.clock_drift) /
            (1 + state.clock_drift))

    def observed_message_types(self):
        return [sirf_messages.NavigationLibrarySVStateData]

    def __call__(self, message):
        self._sv_states[message.satellite_id] = message
