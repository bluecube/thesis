from . import gps
from . import gps_replay
from . import sirf
from . import sirf_messages
from . import nmea
from . import precise_ephemeris


def open_gps(*args, **kwargs):
    """
    Factory function. Tries to open a gps as a replay and if this fails
    tries a real gps.
    """
    try:
        return gps_replay.GpsReplay(*args, **kwargs)
    except IOError:
        pass
    except StopIteration:
        pass

    return gps.Gps(*args, **kwargs)

