from . import sirf
from . import sirf_messages
from . import nmea
from .gps import Gps
from .gps_replay import GpsReplay
from .precise_ephemeris import IGSEphemeris
from .broadcast_ephemeris import BroadcastEphemeris
from .message_observer import MessageObserver
from .message_observer import message_observer_decorator


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

