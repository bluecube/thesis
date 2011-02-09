import struct

class _SirfMessageBase:
    """
    Base class for SIRF messages.
    """

    @classmethod
    def get_message_id(cls):
        raise NotImplementedError()

    @classmethod
    def from_bytes(cls, data):
        raise NotImplementedError()

    def __init__(self, fields):
        """
        Initialize the message with given fields.
        """

        assert fields['message_id'] == self.get_message_id()

        self.__dict__.update(fields)

    def __str__(self):
        return self.__class__.__name__ + str(self.__dict__)


class MeasureNavigationDataOut(_SirfMessageBase):

    packer = struct.Struct('>BiiihhhBBBHIBBBBBBBBBBBBB')
    
    @classmethod
    def get_message_id(cls):
        return 2

    @classmethod
    def from_bytes(cls, data):
        unpacked = cls.packer.unpack(data)

        (message_id, x, y, z, vx, vy, vz, mode1, hdop, mode2, gps_week,
        gps_tow, sv_count) = unpacked[:-12] # skip the last 12 fields

        chprn = []
        for i in range(-12, 0):
            chprn.append(unpacked[i])

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
        del fields['data']
        del fields['cls']
        del fields['unpacked']
        
        return cls(fields)
