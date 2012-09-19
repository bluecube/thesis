import struct

class NamedUnpacker(object):
    """
    A thin wrapper around struct from python std library.
    Fields are named and optionally can contain scale.
    """
    def __init__(self, align, items):
        """Initialize the unpacker.

        align:
            typically '<', or '>', prepended to the struct specification.
        items:
            list of tuples, each specifying a single field.
            Format of the tuple is: (struct field type, name, scaling factor),
            only the first one is required, but fields without name won't show
            up in the result."""

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


