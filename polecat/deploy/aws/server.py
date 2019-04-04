import asyncio

import ujson
from graphql_server.error import HttpQueryError

from ...project import load_project
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
        return {
            'statusCode': result[1],
            'body': ujson.dumps(result[0])
        }
