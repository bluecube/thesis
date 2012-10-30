from . import gps_operations

class RewindableGps(gps_operations.GpsOperations):
    """Class that wraps around a GPS and adds a possibility of rewinding
    the messages.
    """

    exit_rewind_buffer_actions = set(['stop', 'continue'])

    def __init__(self, source, exit_rewind_buffer_action='stop'):
        """ Initialize the rewindable gps.

        source -- the gps providing the messages.
        exit_rewind_buffer_action --
            what happens when leaving the rewind buffer (when a new real message
            would be fetched). Possible values are 'stop', to raise StopIteration,
            and 'continue' to keep going as if nothing has happened."""

        super(RewindableGps, self).__init__()

        if exit_rewind_buffer_action not in self.exit_rewind_buffer_actions:
            raise Exception("exit_rewind_buffer_action must be one of " +
                ', '.join(self.exit_rewind_buffer_actions))
        self._source = source
        self._buffer = []
        self._state = None
            # state is either None. meaning that we are adding to the rewind buffer,
            # or iterator that will provide messages from the rewind buffer
        self._action = exit_rewind_buffer_action

    def is_in_rewind_buffer(self):
        """ Return True if the last message was taken from the rewind buffer,
        False if it came from the source GPS."""
        return self._state is not None

    def set_mark(self):
        """ Set the mark to which the message stream will be rewound. """
        if self.is_in_rewind_buffer():
            raise Exception("Setting the mark inside rewind buffer is not supported")

        self._buffer = []

    def rewind(self):
        """ Rewind the messages to the last mark """
        self._state = iter(self._buffer)

    def _read_binary_sirf_msg(self):
        if self._state is not None:
            try:
                msg, self.last_msg_time = next(self._state)
                return msg
            except StopIteration:
                self._state = None
                if self._action == 'stop':
                    raise

            assert(self._action == 'continue')
            
        msg = self._source._read_binary_sirf_msg()
        self.last_msg_time = self._source.last_msg_time
        self._buffer.append((msg, self.last_msg_time))
        return msg
