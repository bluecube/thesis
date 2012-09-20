class MessageObserver:
    def observed_message_types(self):
        """
        Return a set of sirf message classes that this observer is interested in.
        """
        return set()

    def notify(self, message):
        """
        Notification that a message was received.
        Only the messages specified in observed_message_types() are received.
        """
        raise NotImplementedError()
