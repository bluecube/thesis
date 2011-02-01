import time

def read_message(serial):
    """
    Read a sentence from the gps one 
    fields[0] should be something like 'GPGGA'.
    """
    old_timeout = serial.timeout

    try:
        end_time = time.time() + serial.timeout
        payload_length = _find_beginning(serial, end_time)

        data = _read_with_timeout(serial, payload_length, end_time)

        checksum = sum(data) & 0x7FFF
    
        expected_checksum = _read_end(serial, end_time)

        if checksum != expected_checksum:
            raise Exception("Checksum error.")

        return data
    finally:
        serial.timeout = old_timeout

def _read_with_timeout(serial, count, end_time):
    serial.timeout = end_time - time.time()
    data = serial.read(count)
    if len(data) < count:
        raise Exception("Timed out")
    return data

def _find_beginning(serial, end_time):
    """
    Find a correct beginning sequence of a sirf message.
    Returns length of payload.
    Only way this may fail is timeout; invalid message start
    sequences are ignored.
    """
    status = 0
    length = 0

    while True:
        c = _read_with_timeout(serial, 1, end_time)[0]
        
        if status == 3:
            length |= c
            return length
        elif status == 2 and c <= 0x7F:
            length = c << 8
            status = 3
        elif status == 1 and c == 0xA2:
            status = 2
        elif c == 0xA0:
            status = 1
        else:
            status = 0

def _read_end(serial, end_time):
    """
    Read an end of the message and return checksum.
    This may fail if the end marker is not where we expect it to be.
    """
    data = _read_with_timeout(serial, 4, end_time)
    checksum = data[0] << 8 | data[1]

    if data[2] != 0xB0 or data[3] != 0xB3:
        raise Exception("Invalid end sequence")

    return checksum

def send_message(serial, data):
    """
    Send a sirf message to a serial port.
    data is bytes
    """

    if len(data) > 0x7FFF:
        raise Exception("Message too long.")

    checksum = sum(data) & 0x7FFF

    serial.write(bytes([0xA0, 0xA2, len(data) >> 8, len(data) & 0xFF]))
    serial.write(data)
    serial.write(bytes([checksum >> 8, checksum & 0xFF, 0xB0, 0xB3]))
    serial.flush()
