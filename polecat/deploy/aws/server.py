import asyncio
from jwt import InvalidSignatureError

import ujson
from graphql_server.error import HttpQueryError

from ...project.project import load_project
from .event import LambdaEvent


class LambdaServer:
    def __init__(self, project=None):
        self.project = project or load_project()
        self.project.prepare()

    def handle(self, event, context=None):
        event = LambdaEvent(event)
        if event.request.method == 'OPTIONS':
            return self.handle_cors(event)
        loop = asyncio.get_event_loop()
        try:
            result = loop.run_until_complete(
                self.project.handle_event(event)
            )
        except InvalidSignatureError:
            result = (
                {'errors': ['Unauthorized']},
                401
            )
        except HttpQueryError as e:
            result = (
                {'errors': [e.message]},
                e.status_code
            )
        return self.encode_result(event, result)

    def handle_cors(self, event):
        # TODO: Need to make this more restrictive.
        return {
            'statusCode': '200',
            'body': '',
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET,PUT,POST,PATCH,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Max-Age': '86400'
            }
        }

    def encode_result(self, event, result):
        # TODO: I think separating admin from server makes more sense.
        # I'll come back here and split this out.
        if event.is_admin():
            return result
        body = result[0]
        headers = {
            # TODO: More restrictive.
            'Access-Control-Allow-Origin': '*',
        }
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
