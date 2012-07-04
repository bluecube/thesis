from __future__ import unicode_literals

import time
import logging
import itertools
import gzip

from . import gps_operations

import pickle

class GpsReplay(gps_operations.GpsOperations):
    """
    Replay SIRF messages from a recording.
    """

    def _read_int(self):
        line = next(self._f).rstrip()
        return int(line)

    def _read_float(self):
        line = next(self._f).rstrip()
        return float(line)

    def _read_bytes(self):
        length = self._read_int()
        return self._f.read(length)

    def __init__(self, recording):
        self._logger = logging.getLogger('localization.gps-replay')

        self._f = gzip.GzipFile(recording, 'rb')

        self.start_time = self._read_float()
        self._sirf_version_string = self._read_bytes().decode('ascii')

    def _read_binary_sirf_msg(self):
        """
        Return bytes with a single valid message read from the port.
        Tries to recover after less serious errors.
        Raises StopIteration if there are no more messages to read.
        """

        data = self._read_bytes()
        self.last_msg_time = self._read_float()

        self._logger.debug("Replay message (id = {}) @ {}".format(
            data[0], str(self.last_msg_time)))

        return data

    def __next__(self):
        """
        Replay will stop when we hit EOF.
        """
        return self.read_message()
