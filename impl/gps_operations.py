import sirf
import sirf_messages

class GpsOperations:
    """
    Operations common to both real gps and recording.
    """

    def _read_binary_sirf_msg(self):
        """
        Return bytes with a single valid message read from the port
        (the message payload).
        """
        raise NotImplemented()

    def read_message(self):
        """
        Read one recognized SIRF message from the gps.
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

    def __iter__(self):
        """
        We want to support iterator protocol.
        """
        return self

    def __next__(self):
        """
        We want to support iterator protocol.
        """
        return self.read_message()
