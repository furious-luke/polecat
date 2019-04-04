from ..event import Event


class LambdaEvent(Event):
    def __init__(self, event):
        super().__init__(event)
        self.parse_event()

    def parse_event(self):
        pass
