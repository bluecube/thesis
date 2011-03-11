__all__ = ['gps', 'gps_operations', 'gps_replay',
    'nmea', 'sirf', 'sirf_messages']
    # serial_wrapper is intentionally missing.

import gps.gps
import gps.gps_replay

def open_gps(file):
    """
    Factory function. Tries to open a gps as a replay and if this fails
    tries a real gps.
    """
    try:
        return gps_replay.GpsReplay(file)
    except IOError:
        return gps.Gps(file)

