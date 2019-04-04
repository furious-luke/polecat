class Event:
    def __init__(self, event):
        self.event = event

    def is_http(self):
        return False


class HttpEvent(Event):
    def __init__(self, event, request=None):
        super().__init__(event)
        self.request = request or event

    def is_http(self):
        return True
