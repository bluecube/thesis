import operator
import functools

class NmeaException(Exception):
    def __init__(self, desc):
        self.desc = desc
    def __str__(self):
        return self.desc

def read_sentence(serial):
    """
    Read a sentence from the gps one 
    fields[0] should be something like 'GPGGA'.
    """
    return _parse_sentence(serial.readline())

def send_sentence(serial, fields):
    """
    Send a NMEA message to a serial port.
    fields[0] should be something like 'GPGGA'.
    """
    serial.write(_build_sentence(fields))
    serial.flush()

def _parse_sentence(line):
    """
    Parse a NMEA sentence from a bytearray and return
    a list of fields.
    """

    if line[0] != b'$'[0]:
        raise NmeaException("Missing '$'.")

    if line[-5] != b'*'[0]:
        raise NmeaException("Missing '*'.")

    if line[-2:] != b'\r\n':
        raise NmeaException("Wrong line ending.")


    checksum = functools.reduce(operator.__xor__, line[1:-5])
    expected_checksum = int(line[-4:-2].decode('ascii'), 16)

    if checksum != expected_checksum:
        raise NmeaException("Checksums don't match (computed: " +
            str(checksum) + ", expected: " + str(expected_checksum) + ")")

    return line[1:-5].decode('ascii').split(',')

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
