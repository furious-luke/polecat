from graphql_server import (default_format_error, encode_execution_results,
                            run_http_query)

from ..project.handler import Handler
from .schema import build_graphql_schema


class GraphqlAPI(Handler):
    def prepare(self):
        self.schema = build_graphql_schema()

    def match(self, event):
        # TODO: Use regex
        return event.is_http() and \
           event.request.method == 'POST' and \
           (event.request.path == '/graphql' or
            event.request.path == '/graphql/')

    async def handle_event(self, event):
        # TODO: There's no sync version of this for some reason...
        result = await run_http_query(
            self.schema,
            event.request.method.lower(),
            event.request.json,
            # query_data=None,
            # batch_enabled=False,
            # catch=False,
            context_value={
                'session': event.session
            }
        )
        is_batch = False  # TODO: How to handle this?
        result = encode_execution_results(
            result[0],
            default_format_error,
            is_batch,
            lambda d: d  # pass-through
        )
        # TODO: This is a little ugly.
        if result[0]['errors']:
            result[0]['errors'] = tuple(map(format_error, result[0]['errors']))
        return result


def format_error(error):
    original_error = getattr(error, 'original_error', None)
    if original_error:
        return str(original_error)
    else:
        # TODO: If in debug mode, include path: str(error)
        try:
            return error.message
        except AttributeError:
            return str(error)
