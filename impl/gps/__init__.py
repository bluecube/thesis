from . import gps
from . import gps_replay
from . import sirf
from . import sirf_messages
from . import nmea


def open_gps(file):
    """
    Factory function. Tries to open a gps as a replay and if this fails
    tries a real gps.
    """
    try:
        return gps_replay.GpsReplay(file)
    except IOError:
        return gps.Gps(file)

