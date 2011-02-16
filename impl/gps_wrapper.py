import gps
import gps_replay

class GpsWrapper:
    """
    Either a serial SIRF III GPS or a recording of such GPS.
    """

    def __init__(self, *args, **kwargs):
        try:
            self.__class__ = gps_replay.GpsReplay
            gps_replay.GpsReplay.__init__(self, *args, **kwargs)
        except IOError:
            self.__class__ = gps.Gps
            gps.Gps.__init__(self, *args, **kwargs)
