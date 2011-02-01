import serial
import time
import logging

import nmea
import sirf

class Gps:
    """
    Sirf based GPS
    """

    NMEA_SPEED = 4800
    SIRF_SPEED = 19200
    RETRY_COUNT = 3

    EXPECTED_SPEEDS = (4800, 19200, 9600)
    
    def __init__(self, port, speed):
        self._ser = serial.Serial(port, speed, timeout=1)

        self._logger = logging.getLogger('localization.gps')

        self._mode = ''

        for speed in self.EXPECTED_SPEEDS:
            try:
                self._logger.debug("Trying speed " + str(speed) + ".")
                self._ser.baudrate = speed
                self._detect_mode()
                break
            except Exception:
                pass

        if self._mode == '':
            raise Exception("Mode not recognized")

        if self._mode == 'NMEA':
            self.nmea_to_sirf(self.SIRF_SPEED)
    
    def __del__(self):
        if self._mode == 'SIRF':
            self.sirf_to_nmea(self.NMEA_SPEED)

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
            self._ser.close()
            self._ser.baudrate = speed
            self._ser.open()

        try:
            self._detect_mode()
        finally:
            if self._mode != mode:
                print(self._mode)
                raise Exception("Mode switch failed")


    def _detect_mode(self):
        self._ser.flushInput()
        self._mode = ''
        for i in range(self.RETRY_COUNT):
            try:
                nmea.read_sentence(self._ser)
                self._mode = 'NMEA'
                self._logger.debug(self._mode + " mode detected.")
                return
            except nmea.NmeaException:
                pass

            try:
                sirf.read_message(self._ser)
                self._mode = 'SIRF'
                self._logger.debug(self._mode + " mode detected.")
                return
            except Exception:
                pass

        raise Exception("Mode not recognized")
