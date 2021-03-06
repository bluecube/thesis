from __future__ import unicode_literals

import collections
import logging

from . import sirf
from . import sirf_messages

if bytes == str:
    # This branch is here for python 2.x and to avoid
    # the cost of calls to sirf.bytes_to_message_id
    # This whole business is a little ugly :-)
    _message_id_filter = chr
else:
    _message_id_filter = lambda(x): x

assert _message_id_filter(97) == b'a'[0]

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

    def loop(self, observers, cycle_end_callback = None, cycle_end_threshold = 0.3, log_status = 600):
        """
        Read messages in infinite loop and notify observers.

        observers:
            Iterable of observers that will be notified as messages
            are received
        cycle_end_callback:
            Callable that will be called after the measurement cycle ends, or None.
            Block end callback will only be called when a message arrives with time distance larger
            than block end threshold, not immediately after the time runs out!
        cycle_end_threshold:
            How long a pause between two messages must be to be taken as a start of new measurement cycle.
        log_status:
            After how many cycles should the status be logged.
            If this is false, then no logging is performed.
        """

        observers = list(observers)

        message_ids = {}
        for observer in observers:
            for message_type in observer.observed_message_types():
                filtered_id = _message_id_filter(message_type.get_message_id())

                message_ids.setdefault(filtered_id, []).append(observer)

        if log_status:
            status_id = _message_id_filter(sirf_messages.GeodeticNavigationData.get_message_id())
        else:
            status_id = None
        status_remaining = 0
        last_msg_time = float("nan")

        while True:
            try:
                binary = self._read_binary_sirf_msg()
            except StopIteration:
                return

            if cycle_end_callback is not None and self.last_msg_time - last_msg_time > cycle_end_threshold:
                cycle_end_callback()

            last_msg_time = self.last_msg_time

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

