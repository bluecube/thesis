from __future__ import unicode_literals

import collections
import logging

from . import sirf
from . import sirf_messages

class GpsOperations(collections.Iterator):
    """
    Operations common to both real gps and recording.
    """

    def __init__(self):
        self._logger = logging.getLogger('localization.gps')

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
            if sirf.bytes_to_message_id(data) in ids:
                yield sirf.from_bytes(data)

    def split_to_cycles(self, msg_type_filter = None, separation = 0.5):
        """
        Returns iterator of messages grouped by the measurement cycles
        and optionally filtered only to message types contained in msg_type_filter.
        """

        ids = {msg_type.get_message_id() for msg_type in msg_type_filter}

        if not len(ids):
            class _Everything:
                def __contains__(self, x):
                    return True
            ids = _Everything()

        out = []
        last_msg_time = float("nan")
        while True:
            data = self._read_binary_sirf_msg()

            if sirf.bytes_to_message_id(data) in ids:
                out.append(sirf.from_bytes(data))

            if self.last_msg_time - last_msg_time > separation:
                yield out
                out = []

            last_msg_time = self.last_msg_time

    def loop(self, observers, log_status = 600):
        """
        Read messages in infinite loop and notify observers.

        observers:
            list of observers that will be notified as messages
            are received
        log_status:
            After how many cycles should the status be logged.
            If this is false, then no logging is performed.
        """

        observers = list(observers)

        if bytes == str:
            # This branch is here for python 2.x and to avoid
            # the cost of calls to sirf.bytes_to_message_id
            # This whole business is a little ugly :-)
            message_id_filter = chr
        else:
            message_id_filter = lambda(x): x

        assert message_id_filter(97) == b'a'[0]

        message_ids = {}
        for observer in observers:
            for message_type in observer.observed_message_types():
                filtered_id = message_id_filter(message_type.get_message_id())

                message_ids.setdefault(filtered_id, []).append(observer)

        if log_status:
            status_id = message_id_filter(sirf_messages.GeodeticNavigationData.get_message_id())
        else:
            status_id = None
        status_remaining = 0

        while True:
            try:
                binary = self._read_binary_sirf_msg()
            except StopIteration:
                return

            message_id = binary[0]

            if status_remaining <= 0 and message_id == status_id:
                message = sirf.from_bytes(binary)
                self._logger.info(message.status_line())

                status_remaining = log_status

                if message_id not in message_ids:
                    continue
            else:
                if message_id == status_id:
                    status_remaining -= 1

                if message_id not in message_ids:
                    continue
                else:
                    message = sirf.from_bytes(binary)

            for observer in message_ids[message_id]:
                observer(message)

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

