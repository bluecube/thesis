class MessageObserver:
    def observed_message_types(self):
        """
        Return iterable of sirf message classes that this observer is interested in.
        """
        return []

    def __call__(self, message):
        """
        Notification that a message was received.
        Only the messages specified in observed_message_types() are received.
        """
        raise NotImplementedError()


class MessageCollector(MessageObserver):
    """A class that puts selected message types in its `collected` field"""

    def __init__(self, *observed_message_types):
        self._message_types = observed_message_types
        self.clear()

    def clear(self):
        """Empty the list of collected messages."""
        self.collected = []

    def observed_message_types(self):
        return self._message_types

    def __call__(self, message):
        self.collected.append(message)


def message_observer_decorator(*observed_message_types):
    """Decorator, that turns a ordinary function into an observer."""
    def decorate(func):
        func.observed_message_types = lambda: set(observed_message_types)
        return func
    return decorate
