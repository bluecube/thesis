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

def message_observer(*observed_message_types):
    """Decorator, that turns a ordinary function into an observer."""
    def decorate(func):
        func.observed_message_types = lambda: set(observed_message_types)
        return func
    return decorate
