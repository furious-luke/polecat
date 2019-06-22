import os
import re
from importlib import import_module

from graphql_server import HttpQueryError
from polecat.core.context import active_context
from polecat.model.db.helpers import create_schema
from polecat.model.registry import (access_registry, model_registry,
                                    role_registry)

from ..admin.commands import *  # noqa
from .index import IndexHandler, get_index_html

active_project = None


def get_active_project():
    global active_project
    return active_project


def load_project():
    module_path = os.environ.get('POLECAT_PROJECT_MODULE')
    if module_path is None:
        raise Exception('Please set POLECAT_PROJECT_MODULE')
    parts = module_path.split('.')
    module_name, class_name = '.'.join(parts[:-1]), parts[-1]
    project_class = getattr(import_module(module_name), class_name)
    project = project_class()
    # proxy_project.set_target(project)
    return project


class Project:
    name = None
    bundle = None
    default_role = None
    config = None

    def __init__(self, name=None, default_role=None, config=None):
        self.name = name or self.name
        if not self.name:
            self.name = self.__class__.__name__.lower()
            if self.name.endswith('project'):
                self.name = self.name[:-7]
        self.default_role = default_role or self.default_role
        self.bucket = os.environ.get('BUCKET')
        self.bundle = os.environ.get('BUNDLE', self.bundle)
        self.bundle_version = os.environ.get('BUNDLE_VERSION')
        self.handlers = []
        self.config = config or self.config or {}
        global active_project
        active_project = self

    @property
    def apps(self):
        # TODO: Cache.
        return list(active_context().registries.app_registry)

    @active_context
    def prepare(self, context):
        # TODO: This should be a method on the config, but it would
        # need to have an underscore prefix, which I'm starting to
        # hate.
        for key, value in self.config.items():
            context.config[key] = value
        self.prepare_apps()
        self.prepare_schema()
        # TODO: If not in DEBUG mode, validate settings.
        if not len(self.handlers):
            # TODO: Hmm, don't like the internal import so
            # much... better way to set default handlers? Also,
            # shouldn't be importing AWS middleware here, it should be
            # setup when selecting AWS as deployment system.
            from polecat.deploy.aws.middleware import DevelopMiddleware
            from polecat.auth.middleware import RoleMiddleware
            from polecat.graphql.api import GraphqlAPI
            self.handlers.append(
                GraphqlAPI(
                    self,
                    middleware=[
                        DevelopMiddleware(),
                        RoleMiddleware(self.default_role)
                    ]
                )
            )
        self.handlers.append(IndexHandler(self))
        from polecat.admin.handler import AdminHandler  # TODO: Ugh.
        self.handlers.append(AdminHandler(self))
        for handler in self.handlers:
            handler.prepare()
        self.index_html = self.get_index_html()

    @active_context
    def prepare_apps(self, context=None):
        # TODO: This desperately needs to be cleaned up.
        items = []
        for app in context.registries.app_registry:
            items.append(
                r'\.'.join(app.__module__.split('.')[:-1])
            )
        if not items:
            return
        prog = re.compile('(' + ')|('.join(items) + ')')
        for model in model_registry:
            module_name = r'.'.join(model.__module__.split('.')[:-1])
            match = prog.search(module_name)
            try:
                app = context.registries.app_registry[match.lastindex - 1]
            except AttributeError:
                # TODO: Should we require apps?
                # raise Exception(f'model {model.Meta.name} has no app')
                continue
            app.models.append(model)
            model.Meta.app = app
        for type in context.registries.type_registry:
            module_name = r'.'.join(type.__module__.split('.')[:-1])
            match = prog.search(module_name)
            try:
                app = context.registries.app_registry[match.lastindex - 1]
            except AttributeError:
                # TODO: Should we require apps?
                continue
            app.types.append(model)
            type.Meta.app = app
        for role in role_registry:
            module_name = r'.'.join(role.__module__.split('.')[:-1])
            match = prog.search(module_name)
            try:
                app = context.registries.app_registry[match.lastindex - 1]
            except AttributeError:
                # TODO: Should we require apps?
                continue
            app.roles.append(model)
            role.Meta.app = app
        for access in access_registry:
            module_name = r'.'.join(access.__module__.split('.')[:-1])
            match = prog.search(module_name)
            try:
                app = context.registries.app_registry[match.lastindex - 1]
            except AttributeError:
                # TODO: Should we require apps?
                continue
            app.access.append(access)
            access.app = app

    @active_context
    def prepare_schema(self, context=None):
        context.db.schema = create_schema()

    def get_index_html(self):
        kwargs = {}
        if self.bundle is not None:
            kwargs['bundle'] = self.bundle
        return get_index_html(
            bucket=self.bucket,
            project=self.name,
            bundle_version=self.bundle_version,
            **kwargs
        )

    async def handle_event(self, event):
        for handler in self.handlers:
            if not handler.match(event):
                continue
            return await handler.run(event)
        return await self.default_handler(event)

    async def default_handler(self, event):
        if event.is_http():
            # TODO: Should use a middle-man exception so JSON-API
            # doesn't need to import GraphQL.
            raise HttpQueryError(404, 'Page not found')
        else:
            raise Exception('unhandled event')
