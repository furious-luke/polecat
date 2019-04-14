import os
from importlib import import_module

from graphql_server import HttpQueryError

from .config import default_config

active_project = None


def get_active_project():
    global active_project
    return active_project


def load_project():
    module_path = os.environ.get('POLECAT_PROJECT')
    if module_path is None:
        raise Exception('Please set POLECAT_PROJECT')
    parts = module_path.split('.')
    module_name, class_name = '.'.join(parts[:-1]), parts[-1]
    project_class = getattr(import_module(module_name), class_name)
    project = project_class()
    # proxy_project.set_target(project)
    return project


# TODO: MOve to utils?
def get_handler_func(handler):
    if callable(handler):
        return handler
    else:
        return handler.handle_event


class Project:
    def __init__(self):
        global active_project
        self.config = default_config
        self.handlers = []
        active_project = self

    def prepare(self):
        if not len(self.handlers):
            # TODO: Hmm, don't like the internal import so much...
            from polecat.graphql.api import GraphqlAPI
            self.handlers.append(GraphqlAPI())
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
