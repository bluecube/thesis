import warnings

from . import sirf
from . import sirf_messages
from . import nmea
try:
    import serial
except ImportError:
    have_serial = False
    warnings.warn("Serial port support is not available")
else:
    have_serial = True

if have_serial:
    from .gps import Gps

from .gps_replay import GpsReplay
from .ephemeris import StationState
from .precise_ephemeris import IGSEphemeris
from .broadcast_ephemeris import BroadcastEphemeris
from .message_observer import MessageObserver
from .message_observer import MessageCollector
from .message_observer import message_observer_decorator

from .measurement_error import MeasurementError

from .measurement_error import C

def open_gps(*args, **kwargs):
    """
    Factory function. Tries to open a gps as a replay and if this fails
    tries a real gps.
    """
    if have_serial:
        try:
            return gps_replay.GpsReplay(*args, **kwargs)
        except IOError:
            pass
        except StopIteration:
            pass

        return gps.Gps(*args, **kwargs)
    else:
        return gps_replay.GpsReplay(*args, **kwargs)

