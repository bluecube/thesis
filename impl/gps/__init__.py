__all__ = ['gps', 'gps_operations', 'gps_replay',
    'nmea', 'sirf', 'sirf_messages']
    # serial_wrapper is intentionally missing.

from gps.gps import Gps
from gps.gps_replay import GpsReplay

def open_gps(file):
    """
    Factory function. Tries to open a gps as a replay and if this fails
    tries a real gps.
    """
    try:
        return GpsReplay(file)
    except IOError:
        return Gps(file)

