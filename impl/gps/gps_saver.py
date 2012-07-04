import gzip
import time

from . import open_gps
from . import gps_replay

class GpsSaver:
    """
    Class that saves gps messages to a file.
    """

    def _write_number(self, n):
        self._f.write(repr(n).encode('ascii'))
        self._f.write(b'\n')

    def _write_bytes(self, b):
        self._write_number(len(b))
        self._f.write(b)

    def __init__(self, source_file, target_file):
        self._source = open_gps(source_file)
        self._f = gzip.open(target_file, 'wb')

        if isinstance(self._source, gps_replay.GpsReplay):
            self._write_number(self._source.start_time)
        else:
            self._write_number(time.time())

        self._write_bytes(self._source._sirf_version_string.encode('ascii'))

    def close(self):
        self._f.close()

    def save_message(self):
        """
        Retreive a single message from the GPS and save it.
        Returns the message that was saved.
        """
        msg = self._source._read_binary_sirf_msg()
        self._write_bytes(msg)
        self._write_number(self._source.last_msg_time)
        return msg

    def save_all(self):
        """
        Saves all messages from the gps, until either the recording finishes,
        or exception is thrown (KeyboardInterrupt, probably :-) ).
        """
        try:
            while True:
                self.save_message();
        except StopIteration:
            return
