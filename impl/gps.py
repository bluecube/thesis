import time
import logging
import itertools

import serial
import serial_wrapper

import nmea
import sirf

import sirf_messages

class ModeNotDetectedError(Exception):
    pass

class Gps:
    """
    Sirf based GPS
    """

    NMEA_MODE = ('NMEA', 4800, serial.EIGHTBITS, serial.PARITY_NONE,
        serial.STOPBITS_ONE)
    SIRF_MODE = ('SIRF', 38400, serial.EIGHTBITS, serial.PARITY_NONE,
        serial.STOPBITS_ONE)

    # Modes that will most probably be found.
    # They will be checked in given order.
    #
    # The third mode is added as a way to speed up recoveries after I mess up with the
    # port settings. It happens to be the mode I mostly end up in.
    EXPECTED_MODES = (NMEA_MODE, SIRF_MODE,
        ('NMEA', 38400, serial.EIGHTBITS, serial.PARITY_NONE,
        serial.STOPBITS_ONE))

    # Parameters for port detection if the expected modes didn't work
    # These are listed from the SIRF protocol manual and should
    # cover all possible port options.
    ALL_PROTOCOLS = ('NMEA', 'SIRF')
    ALL_SPEEDS = (4800, 9600, 19200, 38400, 1200, 2400, 57600, 115200)
    ALL_BYTESIZES = (serial.EIGHTBITS, serial.SEVENBITS)
    ALL_PARITIES = (serial.PARITY_NONE, serial.PARITY_EVEN, serial.PARITY_ODD)
    ALL_STOPBITS = (serial.STOPBITS_ONE, serial.STOPBITS_TWO)
    
    def __init__(self, port):
        self._logger = logging.getLogger('localization.gps')

        self._mode = None
        self._ser = serial_wrapper.SerialWrapper(None, timeout=2)
        self._ser.port = port

        self._detect_mode(self.EXPECTED_MODES)

        if self._mode[0] == 'NMEA':
            self._nmea_to_sirf()

    def _log_status(self):
        """
        Put a nice message about the gps status to logs.
        """
        self._logger.info("Mode: " + self._mode_to_string(self._mode) + ".")

    def _mode_to_string(self, mode):
        """
        Convert mode tuple to a string representation
        """
        protocol, speed, bytesize, parity, stopbits = mode
        return protocol + " " + str(speed) + " " + str(bytesize) + \
            str(parity) + str(stopbits)
    
    def __del__(self):
        if not self._mode:
            return

        if self._mode[0] == 'SIRF':
            self._sirf_to_nmea()

    def _nmea_to_sirf(self):
        nmea.send_sentence(self._ser, ("PSRF100", 0, self.SIRF_MODE[1], 8, 1, 0))
        self._switch_mode_internal(self.SIRF_MODE)

    def _sirf_to_nmea(self):
        self.send_message(sirf_messages.SwitchToNmeaProtocol(speed = self.NMEA_MODE[1]))
        self._switch_mode_internal(self.NMEA_MODE)

    def _switch_mode_internal(self, mode):
        self._logger.debug("Switching to " + self._mode_to_string(mode))

        time.sleep(0.5) # settle time for the gps chip
        
        self._detect_mode((mode,))

        if self._mode != mode:
            if self._mode[0] != mode[0]:
                raise Exception("Mode switch failed (detected " + self._mode_to_string(self._mode) + ").")
            else:
                self._logger.warning("Mode switch failed, but the resulting protocol is OK. Continuing.")

    def _detect_mode(self, expected):
        self._logger.debug("Detecting port mode.");
        
        if len(expected):
            i = 0
            for mode in expected:
                i += 1
                if self._try_mode(mode, i, len(expected)):
                    self._mode = mode
                    self._log_status()
                    return

            self._logger.warning("None of the expected modes worked, "
                "will go through all possible modes. This will take a while. Go take a nap.")
        
        total = len(self.ALL_PROTOCOLS) * len(self.ALL_SPEEDS) * \
            len(self.ALL_BYTESIZES) * len(self.ALL_PARITIES) * \
            len(self.ALL_STOPBITS)
        i = 0

        for mode in itertools.product(self.ALL_PROTOCOLS, self.ALL_SPEEDS,
            self.ALL_BYTESIZES, self.ALL_PARITIES, self.ALL_STOPBITS):
            i += 1
            if self._try_mode(mode, i, total):
                self._mode = mode
                self._log_status()
                return

        raise ModeNotDetectedError("Couldn't detect mode.")

    def _try_mode(self, mode, i, count):
        self._logger.debug("Trying " + self._mode_to_string(mode) +
            " (" + str(i) + " / " + str(count) + ").")

        protocol, speed, bytesize, parity, stopbits = mode

        self._ser.close()
        self._ser.baudrate = speed
        self._ser.bytesize = bytesize
        self._ser.parity = parity
        self._ser.stopbits = stopbits
        self._ser.open()

        self._ser.flushInput()

        if protocol == 'NMEA':
            try:
                nmea.read_sentence(self._ser)
                return True
            except nmea.NmeaMessageError as e:
                return False
        elif protocol == 'SIRF':
            try:
                sirf.read_message(self._ser)
                return True
            except sirf.SirfMessageError as e:
                return False
        else:
            raise Exception("Unknown protocol '" + protocol + "'.")

    def read_message(self):
        """
        Read one recognized SIRF message from the serial port.
        """

        if self._mode[0] != 'SIRF':
            raise Exception("Sorry, I can only handle SIRF messages.")
        
        msg = None

        while not msg:
            try:
                msg =  sirf.from_bytes(sirf.read_message(self._ser))
            except sirf.SirfMessageError as e:
                self._logger.warning("Sirf message error (" + str(e) + ").")
            except sirf.UnrecognizedMessageException:
                pass
                
        return msg

    def send_message(self, msg):
        if self._mode[0] != 'SIRF':
            raise Exception("Sorry, I can only handle SIRF messages.")
        
        sirf.send_message(self._ser, msg.to_bytes())
