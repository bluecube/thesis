import gzip
import time

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

    def __init__(self, target_file):
        self._f = gzip.open(target_file, 'wb')
        self._last_msg_time = None
        self._sirf_version_string = None


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

    def init_source(self, source):
        """Try to open a new source.
        Checks if message timestamps and versions are OK
        and raises an exception if they are not.
        This must be called before messages are saved."""

        if isinstance(source, gps_replay.GpsReplay):
            new_start_time = source.start_time
        else:
            new_start_time = time.time()

        if self._sirf_version_string is None:
            assert self._last_msg_time is None

            self._write_number(new_start_time)
            self._write_bytes(source._sirf_version_string.encode('ascii'))

            self._last_msg_time = new_start_time
            self._sirf_version_string = source._sirf_version_string
        else:
            if source.start_time < self._last_msg_time:
                raise Exception("The new source has recording time in the past.")
            if self._sirf_version_string != source._sirf_version_string:
                raise Exception("Version strings do not match!")

        self._source = source

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
