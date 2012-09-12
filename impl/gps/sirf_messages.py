from __future__ import division

import struct
import numpy

from . import serial_wrapper

class _NamedUnpacker(object):
    def __init__(self, align, items):
        self.items = items
        self.struct = struct.Struct(
            align + ''.join((x[0] for x in items)))

    def unpack(self, data):
        unpacked_iter = iter(self.struct.unpack(data))
        ret = {}

        for x in self.items:
            if len(x) <= 1:
                continue

            val = next(unpacked_iter)

            if len(x) >= 3:
                val = val / float(x[2])

            ret[x[1]] = val

        return ret


class _SirfMessageBase(object):
    """
    Base class for all SIRF messages
    """

    @classmethod
    def get_message_id(cls):
        """
        Return an integer with the message id.
        """
        raise NotImplementedError()

    def __init__(self, fields = {}, **kwargs):
        """
        Initialize the message with given fields.
        """
        fields.update(kwargs)

        fields['message_id'] = self.get_message_id()

        self.__dict__.update(fields)

    def __str__(self):
        return self.__class__.__name__ + " " + str(self.__dict__)

    def to_bytes(self):
        """
        Convert message to an array of bytes.
        """
        raise NotImplementedError()


class _SirfReceivedMessageBase(_SirfMessageBase):
    """
    Base class for received SIRF messages.
    """

    def __init__(self, fields, data):
        super(_SirfReceivedMessageBase, self).__init__(fields)
        self.data = data

    @classmethod
    def from_bytes(cls, data):
        """
        Construct the message fom a tuple.
        """
        raise NotImplementedError()

    @classmethod
    def sirf_double(cls, data):
        """
        Convert 8 bytes to a double.
        !!! ONLY WORKS WITH GSW3 CHIPS !!!
        """
        return struct.unpack(">d", data[4:] + data[:4])[0]

    @classmethod
    def sirf_single(cls, data):
        """
        Convert 4 bytes to a single.
        """
        return struct.unpack(">f", data)[0]

    def to_bytes(self):
        """
        Return the bytes that created this message
        """
        return self.data


class _SirfSentMessageBase(_SirfMessageBase):
    """
    Base class for sent SIRF messages.
    """
    pass


class MeasureNavigationDataOut(_SirfReceivedMessageBase):
    packer = struct.Struct('>B3i3hBBBHIB12B')

    @classmethod
    def get_message_id(cls):
        return 2

    @classmethod
    def from_bytes(cls, data):
        unpacked = cls.packer.unpack(data)

        (message_id, x, y, z, vx, vy, vz, mode1, hdop, mode2, gps_week,
        gps_tow, sv_count) = unpacked[:-12] # skip the last 12 fields

        chprn = unpacked[-12:-1]

        assert message_id == 2

        vx /= 8
        vy /= 8
        vz /= 8
        
        dgps = (mode1 & 0x80 != 0)
        dop_mask = (mode1 & 0x40 != 0)
        altmode = (mode1 & 0x30) >> 4
        tpmode = (mode1 & 0x08 != 0)
        pmode = (mode1 & 0x07)
        del mode1

        hdop /= 5

        dr_error = (mode2 & 0xC0)
        alt_hold = (mode2 & 0x20 != 0)
        velocity_invalid = (mode2 & 0x10 != 0)
        solution_edited = (mode2 & 0x08 != 0)
        velocity_dr_timeout = (mode2 & 0x04 != 0)
        solution_validated = (mode2 & 0x02 != 0)
        sensor_dr_used = (mode2 & 0x01 != 0)
        del mode2

        gps_tow /= 100

        pos = numpy.matrix([[float(x), float(y), float(z)]])
        v = numpy.matrix([[vx, vy, vz]])

        fields = locals().copy()
        del fields['cls']
        del fields['data']
        del fields['unpacked']
        
        return cls(fields, data)


class ClockStatusData(_SirfReceivedMessageBase):
    packer = struct.Struct('>BHIBIII')

    @classmethod
    def get_message_id(cls):
        return 7

    @classmethod
    def from_bytes(cls, data):
        unpacked = cls.packer.unpack(data)

        (message_id, extended_gps_week, gps_tow, sv_count, clock_drift,
            clock_bias, estimated_gps_time) = unpacked

        gps_tow /= 100

        fields = locals().copy()
        del fields['cls']
        del fields['data']
        del fields['unpacked']
        
        return cls(fields, data)


class NavigationLibraryMeasurementData(_SirfReceivedMessageBase):
    packer = struct.Struct('>BBIB8s8s4s8sHB10BHHhBB')

    @classmethod
    def get_message_id(cls):
        return 28

    @classmethod
    def from_bytes(cls, data):
        unpacked = cls.packer.unpack(data)

        (message_id, channel, time_tag, satellite_id, gps_sw_time, pseudorange,
            carrier_freq, carrier_phase, time_in_track, sync_flags) = unpacked[:10]
        c_n = unpacked[10:20]
        (delta_range_interval, mean_delta_range_time, extrapolation_time,
            phase_error_count, low_power_count) = unpacked[-5:]

        gps_sw_time = cls.sirf_double(gps_sw_time)
        pseudorange = cls.sirf_double(pseudorange)
        carrier_freq = cls.sirf_single(carrier_freq)
        carrier_phase = cls.sirf_double(carrier_phase)

        # TODO: expand sync flags bit field

        fields = locals().copy()
        del fields['cls']
        del fields['data']
        del fields['unpacked']
        
        return cls(fields, data)

class NavigationLibrarySVStateData(_SirfReceivedMessageBase):
    """
    Satellite positions and speeds.
    """
    packer = struct.Struct('>BB8s8s8s8s8s8s8s8s4sB4x4x4s')

    @classmethod
    def get_message_id(cls):
        return 30

    @classmethod
    def from_bytes(cls, data):
        unpacked = cls.packer.unpack(data)

        (message_id, satellite_id, gps_time, pos_x, pos_y, pos_z, v_x, v_y, v_z,
        clock_bias, clock_drift, ephemeris_flags, iono_delay) = unpacked

        gps_time = cls.sirf_double(gps_time)

        pos_x = cls.sirf_double(pos_x)
        pos_y = cls.sirf_double(pos_y)
        pos_z = cls.sirf_double(pos_z)

        v_x = cls.sirf_double(v_x)
        v_y = cls.sirf_double(v_y)
        v_z = cls.sirf_double(v_z)

        clock_bias = cls.sirf_double(clock_bias)
        clock_drift = cls.sirf_single(clock_drift)

        pos = numpy.matrix([[pos_x, pos_y, pos_z]]) 
        v = numpy.matrix([[v_x, v_y, v_z]])

        iono_delay = cls.sirf_single(iono_delay)

        fields = locals().copy()
        del fields['cls']
        del fields['data']
        del fields['unpacked']
        
        return cls(fields, data)

class GeodeticNavigationData(_SirfReceivedMessageBase):
    packer = _NamedUnpacker('>', [
        ('B', 'message_id'),
        ('H', 'nav_valid'),
        ('H', 'nav_type'),
        ('H', 'extended_gps_week'),
        ('I', 'gps_tow', 1e3),
        ('H', 'utc_year'),
        ('B', 'utc_month'),
        ('B', 'utc_day'),
        ('B', 'utc_hour'),
        ('B', 'utc_minute'),
        ('H', 'utc_second', 1e3),
        ('I', 'sat_ids'),
        ('i', 'latitude', 1e7),
        ('i', 'longitude', 1e7),
        ('i', 'altitude_ellipsoid', 1e2),
        ('i', 'altitude_msl', 1e2),
        ('b', 'map_datum'),
        ('H', 'speed_over_ground', 1e2),
        ('H', 'course_over_ground', 1e2),
        ('xx',),
        ('h', 'climb_rate', 1e2),
        ('h', 'heading_rate', 1e2),
        ('I', 'ehpe', 1e2),
        ('I', 'evpe', 1e2),
        ('I', 'ete', 1e2),
        ('H', 'ehve', 1e2),
        ('i', 'clock_bias', 1e2),
        ('I', 'clock_bias_error', 1e2),
        ('i', 'clock_drift', 1e2),
        ('I', 'clock_drift_error', 1e2),
        ('I', 'distance'),
        ('H', 'distance_error'),
        ('H', 'heading_error'),
        ('x',),
        ('B', 'hdop', 5),
        ('B', 'additional_mode_info')])

    @classmethod
    def get_message_id(cls):
        return 41

    @classmethod
    def from_bytes(cls, data):
        fields = cls.packer.unpack(data)

        bit = 0
        num = fields['sat_ids']
        sat_ids = set()
        while num:
            if num & 1:
                sat_ids.add(bit)
            bit += 1
            num >>= 1

        fields['sat_ids'] = frozenset(sat_ids)
        
        return cls(fields, data)


class SbasParameters(_SirfReceivedMessageBase):
    packer = struct.Struct('>BBBBB8x')

    @classmethod
    def get_message_id(cls):
        return 50

    @classmethod
    def from_bytes(cls, data):
        unpacked = cls.packer.unpack(data)
        (message_id, sbas_prn, sbas_mode, dgps_timeout, flag_bits) = unpacked

        timeout = "User" if (flag_bits & 0x01) else "Default";
        health = "Unhealthy" if (flag_bits & 0x02) else "Healthy";
        correction = flag_bits & 0x04 != 0
        sbas_prn_mode = "User" if (flag_bits & 0x08) else "Default";

        fields = locals().copy()
        del fields['cls']
        del fields['data']
        del fields['unpacked']
        
        return cls(fields, data)

class SoftwareVersionString(_SirfReceivedMessageBase):
    """
    Response to poll message 132
    """
    @classmethod
    def get_message_id(cls):
        return 6

    @classmethod
    def from_bytes(cls, data):
        s = data[1:].decode('ascii').rstrip('\x00').strip()
        return cls({'message_id': data[0], 'string': s}, data)


class CommandAcknowledgment(_SirfReceivedMessageBase):
    """
    Acknowledging command.
    """

    packer = _NamedUnpacker('>', [
        ('B', 'message_id'),
        ('B', 'ack_id')])

    @classmethod
    def get_message_id(cls):
        return 11

    @classmethod
    def from_bytes(cls, data):
        return cls(cls.packer.unpack(data), data)


class CommandNegativeAcknowledgment(_SirfReceivedMessageBase):
    """
    Negative acknowledgement of a command.
    """

    packer = _NamedUnpacker('>', [
        ('B', 'message_id'),
        ('B', 'nack_id')])

    @classmethod
    def get_message_id(cls):
        return 12

    @classmethod
    def from_bytes(cls, data):
        return cls(cls.packer.unpack(data), data)


class SwitchToNmeaProtocol(_SirfSentMessageBase):
    packer = struct.Struct('>BB18BxxH')

    @classmethod
    def get_message_id(cls):
        return 129

    def __init__(self, **kwargs):
        #set some reasonable defaults
        # these are taken from GPSD
        self.mode = 2

        self.gga = 1
        self.gga_checksum = True

        self.gll = 0
        self.gll_checksum = True

        self.gsa = 1
        self.gsa_checksum = True

        self.gsv = 5
        self.gsv_checksum = True

        self.rmc = 1
        self.rmc_checksum = True

        self.vtg = 0
        self.vtg_checksum = True

        self.mss = 0
        self.mss_checksum = True

        self.epe = 0
        self.epe_checksum = True

        self.zda = 0
        self.zda_checksum = True

        self.speed = 4800

        super(SwitchToNmeaProtocol, self).__init__(kwargs)

    def to_bytes(self):
        return self.packer.pack(
            self.get_message_id(),
            self.mode,
            self.gga, (1 if self.gga_checksum else 0),
            self.gll, (1 if self.gll_checksum else 0),
            self.gsa, (1 if self.gsa_checksum else 0),
            self.gsv, (1 if self.gsv_checksum else 0),
            self.rmc, (1 if self.rmc_checksum else 0),
            self.vtg, (1 if self.vtg_checksum else 0),
            self.mss, (1 if self.mss_checksum else 0),
            self.epe, (1 if self.epe_checksum else 0),
            self.zda, (1 if self.zda_checksum else 0),
            self.speed)


class PollSoftwareVersion(_SirfSentMessageBase):
    @classmethod
    def get_message_id(cls):
        return 132

    def to_bytes(self):
        return serial_wrapper.to_bytes([self.get_message_id(), 0])


class SetMessageRate(_SirfSentMessageBase):
    packer = struct.Struct('>BBBBxxxx')

    # constants for mode 
    ONE_MESSAGE = 0
    ONE_MESSAGE_INSTANTLY = 1
    ALL_MESSAGES = 2
    NAV_MESSAGES = 3
    DEBUG_MESSAGES = 4
    NAV_DEBUG_MESSAGES = 5

    # constant for update rate
    DISABLE_MESSAGE = 0

    @classmethod
    def get_message_id(cls):
        return 166
    
    def __init__(self, msg, update_rate = 1):
        #reasonable defaults
        self.msg = msg
        self.mode = self.ONE_MESSAGE
        self.update_rate = update_rate
        super(SetMessageRate, self).__init__({msg: msg, update_rate: update_rate})

    def to_bytes(self):
        return self.packer.pack(
            self.get_message_id(),
            self.mode,
            self.msg.get_message_id(),
            self.update_rate)
