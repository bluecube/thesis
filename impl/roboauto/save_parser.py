"""
save_parser.py

Parser for roboauto saves.
Enumerates packet classes in packets.py
"""

import packets
import struct

def parse(filename):
    f = open(filename, 'rb')
    header_struct = struct.Struct('<BBI')

    while True:
        header = f.read(header_struct.size)
        if not len(header):
            return

        sync, packet_type, length = header_struct.unpack(header)
        assert sync == 0xff
        data = f.read(length)

        if packet_type in _packet_types:
            yield _packet_types[packet_type].from_bytes(data)
        else:
            yield UnrecognizedPacket(packet_type)


class UnrecognizedPacket(packets._PacketBase):
    def __init__(self, packet_type):
        self.packet_type = packet_type

    def get_packet_type(self):
        return self.packet_type

    def __str__(self):
        return "UnrecognizedPacket ({:#x})".format(self.packet_type)


# Enumeration of all available packet types
_packet_types = {}
for v in vars(packets).values():
    try:
        if v != packets._PacketBase and \
            issubclass(v, packets._PacketBase):

            _packet_types[v.get_packet_type()] = v
    except TypeError:
        pass

