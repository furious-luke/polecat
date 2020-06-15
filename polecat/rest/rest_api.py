from ..project.handler import Handler

from .schema_builder import RestSchemaBuilder
from .execute import run_http_query


class RestAPI(Handler):
    def prepare(self):
        self.schema = RestSchemaBuilder().build()

    def match(self, event):
        # TODO: Use regex
        return event.is_http() and \
            (event.request.method == 'GET' or
             event.request.method == 'POST' or
             event.request.method == 'PUT' or
             event.request.method == 'PATCH' or
             event.request.method == 'DELETE') and \
            event.request.path.startswith('/rest/')

    async def handle_event(self, event):
        result = await run_http_query(
            self.schema,
            event.request,
            context_value={
                'event': event,
                'session': event.session
            }
        )
        # is_batch = False
        # result = encode_execution_results(
        #     result,
        #     is_batch
        # )
        # # TODO: This is a little ugly.
        # if result[0]['errors']:
        #     result[0]['errors'] = tuple(map(format_error, result[0]['errors']))
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
