import ujson

from ...core.context import active_context
from ..event import Event


class APIGatewayRequest:
    def __init__(self, event):
        self.parse_event(event)

    @active_context
    def parse_event(self, event, context):
        # TODO: Move to config. Also wrong.
        try:
            self.path = event['path']
            self.method = event['httpMethod']
            self.headers = event.get('headers', {})
            self.host = self.headers.get('Host', None)
            self.query_parameters = event.get('queryStringParameters', None)
            self.body = event.get('body', None)
            self.json = ujson.loads(self.body) if self.body is not None else None
            self.is_valid = True
            # TODO: There must be a better way of doing this.
            if context.config.debug:
                if self.path[:8] == '/LATEST/':
                    self.path = self.path[7:]
                elif self.path[:7] == '/LATEST' and len(self.path) == 7:
                    self.path = '/'
        except KeyError:
            self.is_valid = False
            self.host = None
            self.path = None
            self.method = None
            self.headers = {}


class LambdaEvent(Event):
    def __init__(self, event):
        super().__init__(event)
        self.request = APIGatewayRequest(event)

    def is_http(self):
        return self.request.is_valid

    def is_admin(self):
        return self.event.get('event') == 'admin'

    def get_authorization_header(self):
        return self.request.headers.get('Authorization', None)
