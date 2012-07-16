from __future__ import unicode_literals

import collections

from . import sirf
from . import sirf_messages

class GpsOperations(collections.Iterator):
    """
    Operations common to both real gps and recording.
    """

    def _read_binary_sirf_msg(self):
        """
        Return bytes with a single valid message read from the port
        (the message payload).
        """
        raise NotImplemented()

    def set_message_rate(self, msg_type, rate):
        """
        Set how often a message gets sent by the SIRF chip.
        Rate is integer, meaning number of seconds, 0 means disabled.
        This is a no-op unless we are on a real gps.
        """
        pass

    def try_read_message(self):
        """
        Try to read one SIRF message from the gps.
        Raises UnrecognizedMessageException.
        """
        return sirf.from_bytes(self._read_binary_sirf_msg())

    def read_message(self):
        """
        Read one recognized SIRF message from the gps.
        """

        while True:
            try:
                return sirf.from_bytes(self._read_binary_sirf_msg())
            except sirf.UnrecognizedMessageException:
                pass

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
            #print(msg)
                
        return msg

    def filtered_messages(self, msg_type_set):
        """
        Returns iterator of messages of types in msg_type_set.
        Faster than filtering using isinstance.
        """
        ids = {msg_type.get_message_id() for msg_type in msg_type_set}
        
        while True:
            data = self._read_binary_sirf_msg()
            while sirf.bytes_to_message_id(data) not in ids:
                data = self._read_binary_sirf_msg()
            
            yield sirf.from_bytes(data)

    def __next__(self):
        """
        We want to support iterator protocol.
        """
        return self.read_message()

    def next(self):
        """
        Iterator protocol for python 2.x
        """
        return self.read_message()

