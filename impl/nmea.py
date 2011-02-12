import operator
import functools
import time
import serial_wrapper

class NmeaMessageError(Exception):
    pass

def read_sentence(serial):
    """
    Read a NMEA sentence from the gps.
    Returns list of fields.
    """
    old_timeout = serial.timeout

    try:
        end_time = time.time() + serial.timeout

        serial.read_until(b'\\$', end_time)

        line = serial.read_until(b'\\n', end_time)

        if len(line) < 5:
            raise NmeaMessageError("Message too short.")
        
        if line[-5] != b'*'[0]:
            raise NmeaMessageError("Missing '*'.")

        if line[-2:] != b'\r\n':
            raise NmeaMessageError("Wrong line ending.")

        checksum = functools.reduce(operator.__xor__, line[0:-5])
        expected_checksum = int(line[-4:-2].decode('ascii'), 16)

        if checksum != expected_checksum:
            raise NmeaMessageError("Checksum error")

        return line[1:-5].decode('ascii').split(',')
    except serial_wrapper.SerialWrapperTimeout:
        raise NmeaMessageError("Timed out.")
    finally:
        serial.timeout = old_timeout

def send_sentence(serial, fields):
    """
    Send a NMEA message to a serial port.
    fields[0] should be something like 'GPGGA'.
    """
    sentence = _build_sentence(fields)
    serial.write(sentence)
    serial.flush()

def _build_sentence(fields):
    """
    Construct a NMEA message. No field may contain ','.
    """
    
    fields = list(map(str, fields))

    for field in fields:
        if field.find(',') != -1:
            raise NmeaException("Fields may not contain ','.")

    line = ",".join(fields).encode('ascii')

    checksum = functools.reduce(operator.__xor__, line)

    return "$".encode('ascii') + line + \
        "*{:02X}\r\n".format(checksum).encode('ascii')
