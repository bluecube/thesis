import struct

class _SirfMessage:
    """
    Base class for SIRF messages.
    This is only here to be able to iterate through all known message types.
    """

    @classmethod
    def get_message_id(cls):
        raise NotImplementedError()

    @classmethod
    def from_bytes(cls, data):
        raise NotImplementedError()

class MeasureNavigationDataOut(_SirfMessage):

    unpacker = struct.Struct('>BiiihhhBBBHIBBBBBBBBBBBBB')
    
    @classmethod
    def get_message_id(cls):
        return 2

    @classmethod
    def from_bytes(cls, data):
        (message_id, x, y, z, vx, vy, vz, mode1, hdop, mode2, gps_week,
        gps_tow, sv_count, ch1prn, ch2prn, ch3prn, ch4prn, ch5prn, ch6prn, ch7prn,
        ch8prn, ch9prn, ch10prn, ch11prn, ch12prn) = cls.unpacker.unpack(data)

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
        
        ret = cls()
        ret.__dict__ = fields

        return ret
