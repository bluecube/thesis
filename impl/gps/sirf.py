import time
import struct
import logging

from . import serial_wrapper
from . import sirf_messages

_logger = logging.getLogger('localization.gps')

class SirfMessageError(Exception):
    pass

class UnrecognizedMessageException(Exception):
    pass

def read_message(serial):
    """
    Read a sirf sentence from the gps, return the payload data
    or raise an SirfMessageError exception.
    """
    old_timeout = serial.timeout

    try:
        end_time = time.time() + serial.timeout

        serial.read_until(serial_wrapper.to_bytes([0xA0, 0xA2]), end_time)

        length = struct.unpack('>H', serial.read_with_timeout(2, end_time))[0]

        data = serial.read_with_timeout(length, end_time)
        checksum = sum(data) & 0x7FFF
        expected_checksum = struct.unpack('>H',
            serial.read_with_timeout(2, end_time))[0]

        if checksum != expected_checksum:
            raise SirfMessageError('Invalid checksum.')

        message_ending = serial.read_with_timeout(2, end_time)
        if message_ending != serial_wrapper.to_bytes([0xB0, 0xB3]):
            raise SirfMessageError('Invalid message end sequence.')

        return data
    except serial_wrapper.SerialWrapperTimeout:
        raise SirfMessageError("Malformed message (timeout).")
    finally:
        serial.timeout = old_timeout

def send_message(serial, data):
    """
    Send a sirf message to a serial port.
    data is bytes
    """

    if len(data) > 0x7FFF:
        raise Exception("Message too long.")

    checksum = sum(data) & 0x7FFF

    serial.write(serial_wrapper.to_bytes([0xA0, 0xA2, len(data) >> 8, len(data) & 0xFF]))
    serial.write(data)
    serial.write(serial_wrapper.to_bytes([checksum >> 8, checksum & 0xFF, 0xB0, 0xB3]))
    serial.flush()


if isinstance(b'0'[0], str):
    def bytes_to_message_id(data):
        return ord(data[0])
else:
    def bytes_to_message_id(data):
        return data[0]
    

def from_bytes(data):
    """
    Factory method that returns an sirf message object from its
    binary representation.
    data: Payload of the sirf message.
    """

    message_id = bytes_to_message_id(data)


    if not message_id in message_types:
        raise UnrecognizedMessageException("Unrecognized message " +
            str(message_id) + ".")

    _logger.debug("Found message, ID = " + str(message_id) + ".")

    klass = message_types[message_id]

    output = klass.from_bytes(data)

    return output

# Enumeration of all available messages:
message_types = {}
for v in vars(sirf_messages).values():
    try:
        if v != sirf_messages._SirfReceivedMessageBase and \
            issubclass(v, sirf_messages._SirfReceivedMessageBase):

            message_types[v.get_message_id()] = v
    except TypeError:
        pass

