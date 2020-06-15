from polecat.model.db import S
from polecat.model.resolver import APIContext


class RestAPIContext(APIContext):
    def __init__(self, field, event, session, **kwargs):
        super().__init__()
        self.field = field
        self.event = event
        self.session = session
        self.kwargs = kwargs

    def parse_argument(self, name):
        return self.kwargs.get(name)

    def parse_input(self):
        return self.event.request.json

    def get_selector(self):
        # TODO: Use return type from mutation.
        return S()

    @property
    def mutation(self):
        return self.field

    @property
    def query(self):
        return self.field
