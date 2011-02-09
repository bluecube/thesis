import time
import logging

import serial_wrapper

import nmea
import sirf

import sirf_messages

class DetectModeException(Exception):
    pass

class Gps:
    """
    Sirf based GPS
    """

    NMEA_SPEED = 4800
    SIRF_SPEED = 19200
    RETRY_COUNT = 2

    EXPECTED_SPEEDS = (4800, 19200, 9600)
    
    def __init__(self, port):
        self._mode = 'unknown'
        self._logger = logging.getLogger('localization.gps')

        self._ser = serial_wrapper.SerialWrapper(port, timeout=2)

        for speed in self.EXPECTED_SPEEDS:
            try:
                self._logger.debug("Trying " + str(speed) + " baud.")
                self._ser.baudrate = speed
                self._detect_mode()
                break
            except DetectModeException:
                pass

        if self._mode == 'unknown':
            raise DetectModeException("Mode not recognized at any speed.")
            self._ser.close()

        if self._mode == 'NMEA':
            self.nmea_to_sirf()

        self._log_status()

    def _log_status(self):
        """
        Put a nice message about the gps status to logs.
        """
        self._logger.info("GPS in " + self._mode +
            " mode, at " + str(self._ser.baudrate) + " baud.")
    
    def __del__(self):
        if self._mode == 'SIRF':
            self.sirf_to_nmea()

        try:
            self._log_status()
        except:
            pass

    def nmea_to_sirf(self):
        nmea.send_sentence(self._ser, ("PSRF100", 0, self.SIRF_SPEED, 8, 1, 0))

        self._switch_mode_internal('SIRF', self.SIRF_SPEED)

    def sirf_to_nmea(self):
        self.send_message(sirf_messages.SwitchToNmeaProtocol(speed = self.NMEA_SPEED))

        self._switch_mode_internal('NMEA', self.NMEA_SPEED)

    def _switch_mode_internal(self, mode, speed):
        self._logger.debug("Switching to " + mode)

        time.sleep(0.5) # settle time for the gps chip
        
        if speed != self._ser.baudrate:
            self._ser.baudrate = speed

        self._detect_mode()

        if self._mode != mode:
            raise Exception("Mode switch failed (detected mode '" + self._mode + "')")

    def _detect_mode(self):
        self._ser.flushInput()
        self._mode = 'unknown'
        for i in range(self.RETRY_COUNT):
            try:
                nmea.read_sentence(self._ser)
                self._mode = 'NMEA'
                self._logger.debug(self._mode + " mode detected.")
                return
            except nmea.NmeaMessageError as e:
                pass

            try:
                sirf.read_message(self._ser)
                self._mode = 'SIRF'
                self._logger.debug(self._mode + " mode detected.")
                return
            except sirf.SirfMessageError as e:
                pass

        raise DetectModeException("Mode not recognized")

    def read_message(self):
        """
        Read one recognized SIRF message from the serial port.
        """

        if self._mode != 'SIRF':
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
        if self._mode != 'SIRF':
            raise Exception("Sorry, I can only handle SIRF messages.")
        
        sirf.send_message(self._ser, msg.to_bytes())
