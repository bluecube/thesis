from __future__ import division

import named_unpacker

class _PacketBase(object):
    """
    Base class for all Roboauto messages
    """

    @classmethod
    def get_packet_type(cls):
        """
        Return an integer with the packet type.
        """
        raise NotImplementedError()

    @classmethod
    def from_bytes(cls, data):
        """
        Construct the packet fom a tuple.
        """
        raise NotImplementedError()

    def __init__(self, fields = {}, **kwargs):
        """
        Initialize the message with given fields.
        """
        fields.update(kwargs)
        self.__dict__.update(fields)

    def __str__(self):
        return self.__class__.__name__ + " " + str(self.__dict__)


class GPSMeasurement(_PacketBase):
    packer = named_unpacker.NamedUnpacker('<', [
        ('Q', 'timestamp', 1000),
        ('B', 'sat_in_view'),
        ('Q', 'utc', 1000),
        ('?', 'gps_fix'),
        ('i', 'lat', 10000000),
        ('i', 'lon', 10000000),
        ('H', 'alt'),
        ('H', 'tc'),
        ('H', 'gs')])

    @classmethod
    def get_packet_type(cls):
        return 0x20

    @classmethod
    def from_bytes(cls, data):
        return cls(cls.packer.unpack(data))


class OdometerMeasurement(_PacketBase):
    packer = named_unpacker.NamedUnpacker('<', [
        ('Q', 'timestamp', 1000),
        ('i', 'distance_units'),
        ('i', 'distance_centimeters'),
        ('i', 'actual_speed_m_per_s', 1000)])

    @classmethod
    def get_packet_type(cls):
        return 0x40

    @classmethod
    def from_bytes(cls, data):
        return cls(cls.packer.unpack(data))

class Driver(_PacketBase):
    packer = named_unpacker.NamedUnpacker('<', [
        ('Q', 'timestamp', 1000),
        ('?', 'reverse'),
        ('b', 'engines'),
        ('b', 'steering'),
        ('B', 'blinking'),
        ('H', 'errors')])

    @classmethod
    def get_packet_type(cls):
        return 0x60

    @classmethod
    def from_bytes(cls, data):
        return cls(cls.packer.unpack(data))
