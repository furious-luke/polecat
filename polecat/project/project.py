from graphql_server import HttpQueryError
from polecat.graphql.api import GraphqlAPI

active_project = None


def get_active_project():
    global active_project
    return active_project


# TODO: MOve to utils?
def get_handler_func(handler):
    if callable(handler):
        return handler
    else:
        return handler.handle_event


class Project:
    def __init__(self):
        global active_project
        # TODO: Configuration.
        # TODO: Move this into an API class. It should handle init,
        # setup, and teardown.
        self.handlers = [
            GraphqlAPI()
        ]
        active_project = self

    def prepare(self):
        for handler in self.handlers:
            handler.prepare()

    async def handle_event(self, event):
        for handler in self.handlers:
            result = await get_handler_func(handler)(event)
            if result is not None:
                return result
        return await self.default_handler(event)

    async def default_handler(self, event):
        if event.is_http():
            # TODO: Should use a middle-man exception so JSON-API doesn't need to import GraphQL.
            raise HttpQueryError(404, 'Page not found')
        else:
            raise Exception('unhandled event')
