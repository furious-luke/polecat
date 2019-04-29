import asyncio

import ujson
from graphql_server.error import HttpQueryError

from ...project.project import load_project
from .event import LambdaEvent


class LambdaServer:
    def __init__(self):
        self.project = load_project()
        self.project.prepare()

    def handle(self, event, context=None):
        loop = asyncio.get_event_loop()
        try:
            result = loop.run_until_complete(
                self.project.handle_event(LambdaEvent(event))
            )
        except HttpQueryError as e:
            result = (
                {'errors': [e.message]},
                e.status_code
            )
        return self.encode_result(result)

    def encode_result(self, result):
        body = result[0]
        headers = {}
        content_type = result[2] if len(result) > 2 else None
        if content_type != 'text/html':
            body = ujson.dumps(body)
        elif content_type is not None:
            headers['content-type'] = 'text/html'
        return {
            'statusCode': result[1],
            'body': body,
            'headers': headers
        }
