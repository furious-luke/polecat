import ujson

from ..event import Event


class APIGatewayRequest:
    def __init__(self, event):
        self.parse_event(event)

    def parse_event(self, event):
        try:
            self.path = event['path']
            self.method = event['httpMethod']
            self.headers = event.get('headers', {})
            self.query_parameters = event.get('queryStringParameters', None)
            self.body = event.get('body', None)
            self.json = ujson.loads(self.body) if self.body is not None else None
            self.is_valid = True
        except KeyError:
            self.is_valid = False


class LambdaEvent(Event):
    def __init__(self, event):
        super().__init__(event)
        self.request = APIGatewayRequest(event)

    def is_http(self):
        return self.request.is_valid
