import struct

class _SirfMessageBase:
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

        if 'message_id' in fields:
            assert fields['message_id'] == self.get_message_id()
        if 'message_id' in kwargs:
            assert kwargs['message_id'] == self.get_message_id()
        else:
            fields['message_id'] = self.get_message_id()

        self.__dict__.update(fields)
        self.__dict__.update(kwargs)

    def __str__(self):
        return self.__class__.__name__ + " " + str(self.__dict__)


class _SirfReceivedMessageBase(_SirfMessageBase):
    """
    Base class for received SIRF messages.
    """

    @classmethod
    def from_tuple(cls, data):
        """
        Construct the message fom a tuple.
        """
        raise NotImplementedError()


class _SirfSentMessageBase(_SirfMessageBase):
    def to_bytes(self):
        """
        Convert message to an array of bytes.
        """
        raise NotImplementedError()


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
        sensor_dr_used = (mode2 & 0x01 != 0) # TODO: ... whatever this means
        del mode2

        gps_tow /= 100

        fields = locals().copy()
        del fields['cls']
        del fields['data']
        del fields['unpacked']
        
        return cls(fields)


class SoftwareVersionString(_SirfReceivedMessageBase):
    """
    Response to poll message 132
    """

    @classmethod
    def get_message_id(cls):
        return 6

    @classmethod
    def from_bytes(cls, data):
        return cls(string = data[1:].decode('ascii'))

class SwitchToNmeaProtocol(_SirfSentMessageBase):
    packer = struct.Struct('>BB18BxxH')

    @classmethod
    def get_message_id(cls):
        return 129

    def __init__(self, fields = {}, **kwargs):
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

        fields.update(kwargs)

        super().__init__(fields)

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
        return bytes([self.get_message_id(), 0])
