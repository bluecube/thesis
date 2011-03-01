import time
import logging
import itertools
import gzip

import sirf
import sirf_messages

from gps_operations import GpsOperations

import pickle

class GpsReplay(GpsOperations):
    """
    Replay SIRF messages from a recording.
    """

    def __init__(self, recording):
        self._logger = logging.getLogger('localization.gps-replay')

        self._f = gzip.GzipFile(recording, 'rb')

        self._start_time = pickle.load(self._f)
        self._sirf_version_string = pickle.load(self._f)

    def _read_binary_sirf_msg(self):
        """
        Return bytes with a single valid message read from the port.
        Tries to recover after less serious errors.
        """
        
        timestamp, data = self._sirf_version_string = pickle.load(self._f)
        self._logger.debug("Replay message (id = " + str(data[0]) + ") @ " + str(timestamp))

        return data

    def __next__(self):
        """
        Replay will stop when we hit EOF.
        """
        try:
            return self.read_message()
        except EOFError:
            raise StopIteration
