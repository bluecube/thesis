import serial
import time
import re

class SerialWrapperTimeout(Exception):
    pass

class SerialWrapper(serial.Serial):
    """
    Wrapper around the pyserial port supporting a few more 
    functions and absolute timeouts.
    """

    BLOCK_SIZE = 64

    def __init__(self, *args, **kwargs):
        serial.Serial.__init__(self, *args, **kwargs)

        self._wrapper_buffer = b''

    def flushInput(self):
        super(SerialWrapper, self).flushInput()
        self._wrapper_buffer = b''

    def _raw_read_with_timeout(self, count, end_time):
        """
        Read something from the port with given time limit.
        This method doesn't use the output buffer.
        """
        timeout = end_time - time.time()
        if timeout <= 0:
            raise SerialWrapperTimeout()

        self.timeout = timeout
        data = self.read(count)

        if len(data) < count:
            raise SerialWrapperTimeout()

        return data

    def read_with_timeout(self, count, end_time):
        """
        Read from the port with given time limit.
        """

        if len(self._wrapper_buffer) >= count:
            output = self._wrapper_buffer[:count]
            self._wrapper_buffer = self._wrapper_buffer[count:]
        else:
            output = self._wrapper_buffer
            output += self._raw_read_with_timeout(count - len(output), end_time)
            self._wrapper_buffer = b''

        assert len(output) == count

        return output

    def read_until(self, regex, end_time):
        """
        Read characters until regexp is matched or time limit is reached.
        Returns bytes with the read data or raises SerialWrapperTimeout exception.
        The matched string is a part of the returned value.
        """
        
        compiled = re.compile(regex)

        found = compiled.search(self._wrapper_buffer)
        while not found:
            self._wrapper_buffer += self._raw_read_with_timeout(
                self.BLOCK_SIZE, end_time)
            found = compiled.search(self._wrapper_buffer)
        
        output = self._wrapper_buffer[:found.end()]
        self._wrapper_buffer = self._wrapper_buffer[found.end():]

        return output

to_bytes = serial.to_bytes
