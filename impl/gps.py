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
    RETRY_COUNT = 3

    EXPECTED_SPEEDS = (4800, 19200, 9600)
    
    def __init__(self, port):
        self._ser = serial_wrapper.SerialWrapper(port, timeout=2)

        self._logger = logging.getLogger('localization.gps')

        self._mode = 'unknown'

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

        if self._mode == 'NMEA':
            self.nmea_to_sirf(self.SIRF_SPEED)

        self._log_status()

    def _log_status(self):
        """
        Put a nice message about the gps status to logs.
        """
        self._logger.info("GPS in " + self._mode +
            " mode, at " + str(self._ser.baudrate) + " baud.")
    
    def __del__(self):
        if self._mode == 'SIRF':
            self.sirf_to_nmea(self.NMEA_SPEED)
        self._log_status()

    def nmea_to_sirf(self, speed):
        nmea.send_sentence(self._ser, ("PSRF100", 0, speed, 8, 1, 0))

        self._switch_mode_internal('SIRF', speed)

    def sirf_to_nmea(self, speed):
        sirf.send_message(self._ser, bytes([
            0x81,
            0x02, # Don't change nmea debug messages settings
            0x01, 0x01, # GGA
            0x00, 0x00, # suppress GLL
            0x01, 0x01, # GSA
            0x05, 0x01, # GSV
            0x01, 0x01, # RMC
            0x00, 0x00, # suppress VTG
            0x00, 0x01, # suppress MSS
            0x00, 0x01, # suppress EPE
            0x00, 0x01, # suppress ZDA
            0x00, 0x00, # unused
            speed >> 8, speed & 0xff # speed
        ]))

        self._switch_mode_internal('NMEA', speed)

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
            self._logger.debug("Trying NMEA mode")
            try:
                nmea.read_sentence(self._ser)
                self._mode = 'NMEA'
                self._logger.debug(self._mode + " mode detected.")
                return
            except nmea.NmeaMessageError as e:
                pass

            self._logger.debug("Trying SIRF mode")
            try:
                sirf.read_message(self._ser)
                self._mode = 'SIRF'
                self._logger.debug(self._mode + " mode detected.")
                return
            except sirf.SirfMessageError as e:
                pass

        raise DetectModeException("Mode not recognized")

    def get_one(self):
        if self._mode != 'SIRF':
            raise Exception("Sorry, I can only handle SIRF messages.")
        
        return sirf.from_bytes(sirf.read_message(self._ser))
