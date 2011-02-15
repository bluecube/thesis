import time
import logging
import itertools
import gzip

import sirf
import sirf_messages

import pickle

class GpsReplay:
    """
    Replay SIRF messages from a recording.
    """

    def __init__(self, recording, with_timing = True):
        self._logger = logging.getLogger('localization.gps-replay')
        self._with_timing = with_timing

        self._f = gzip.GzipFile(recording, 'rb')

        self._start_time = pickle.load(self._f)
        self._sirf_version_string = pickle.load(self._f)

    def _read_binary_sirf_msg(self):
        """
        Return bytes with a single valid message read from the port.
        Tries to recover after less serious errors.
        """
        
        # TODO: timing
        timestamp, data = self._sirf_version_string = pickle.load(self._f)

        return data

    def read_message(self):
        """
        Read one recognized SIRF message from the serial port.
        """

        msg = None
        
        while not msg:
            try:
                msg = sirf.from_bytes(self._read_binary_sirf_msg())
            except sirf.UnrecognizedMessageException:
                pass
                
        return msg

    def read_specific_message(self, msg_type):
        """
        Discards messages until one of given type is received.
        May block for a long time, careful with this.
        """

        if not issubclass(msg_type, sirf_messages._SirfReceivedMessageBase):
            raise TypeError("msg_type must be a message type.")

        msg = None
        
        while not isinstance(msg, msg_type):
            msg = self.read_message()
                
        return msg

    def messages(self):
        while True:
            yield self.read_message()
