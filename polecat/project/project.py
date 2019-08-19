import os
import re
from importlib import import_module

from graphql_server import HttpQueryError
from polecat.admin.commands import *  # noqa
from polecat.core.config import default_config
from polecat.core.context import active_context
from polecat.db.role_prefix import set_role_prefix
from polecat.model import default_blueprint
from polecat.model.db.helpers import create_schema
from polecat.utils import get_class_path

from .index import IndexHandler, get_index_html

active_project = None


def get_active_project():
    global active_project
    return active_project


def set_active_project(project):
    global active_project
    active_project = project


def load_project():
    global active_project
    if active_project:
        return active_project
    module_path = os.environ.get('POLECAT_PROJECT_MODULE')
    if module_path is None:
        raise Exception('Please set POLECAT_PROJECT_MODULE')
    parts = module_path.split('.')
    module_name, class_name = '.'.join(parts[:-1]), parts[-1]
    project_class = getattr(import_module(module_name), class_name)
    project = project_class()
    active_project = project
    # proxy_project.set_target(project)
    return project


def setup_project():
    project = load_project()
    project.prepare()
    return project


class Project:
    name = None
    deployment = None
    bundle = None
    default_role = None
    config = None

    def __init__(self, name=None, deployment=None, default_role=None, config=None):
        self.models = {}  # TODO: Will remove later.
        self.name = name or self.name
        if not self.name:
            self.name = self.__class__.__name__.lower()
            if self.name.endswith('project'):
                self.name = self.name[:-7]
        self.deployment = deployment or self.deployment
        if not self.deployment:
            self.deployment = os.environ.get('DEPLOYMENT', '')
        self.default_role = default_role or self.default_role
        self.bucket = os.environ.get('BUCKET')
        self.bundle = os.environ.get('BUNDLE', self.bundle)
        self.bundle_version = os.environ.get('BUNDLE_VERSION')
        self.handlers = []
        self.config = config or self.config or {}

    @property
    def apps(self):
        # TODO: Cache.
        return list(active_context().registries.app_registry)

    @property
    def path(self):
        return get_class_path(self.__class__)

    def prepare(self):
        if getattr(self, '_prepared', False):
            return
        self._prepared = True
        set_role_prefix(f'{self.name}_{self.deployment}')
        # TODO: This should be a method on the config, but it would
        # need to have an underscore prefix, which I'm starting to
        # hate.
        for key, value in self.config.items():
            default_config[key] = value
        self.prepare_apps()
        self.prepare_blueprint()
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
        self.prepare_resolvers()

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
        for model in default_blueprint.iter_models():
            module_name = r'.'.join(model.__module__.split('.')[:-1])
            match = prog.search(module_name)
            try:
                app = context.registries.app_registry[match.lastindex - 1]
            except AttributeError:
                # TODO: Should we require apps?
                # raise Exception(f'model {model.Meta.name} has no app')
                # TODO: I should be able to remove this once I get
                # models into the app context.
                self.models[model.Meta.name] = model
                continue
            app.models.append(model)
            model.Meta.app = app
            # TODO: I should be able to remove this once I get models
            # into the app context.
            self.models[f'{app.name}.{model.Meta.name}'] = model
        for type in default_blueprint.iter_types():
            module_name = r'.'.join(type.__module__.split('.')[:-1])
            match = prog.search(module_name)
            try:
                app = context.registries.app_registry[match.lastindex - 1]
            except AttributeError:
                # TODO: Should we require apps?
                continue
            app.types.append(model)
            type.Meta.app = app
        for role in default_blueprint.iter_roles():
            module_name = r'.'.join(role.__module__.split('.')[:-1])
            match = prog.search(module_name)
            try:
                app = context.registries.app_registry[match.lastindex - 1]
            except AttributeError:
                # TODO: Should we require apps?
                continue
            app.roles.append(model)
            role.Meta.app = app
        for access in default_blueprint.iter_access():
            module_name = r'.'.join(access.__module__.split('.')[:-1])
            match = prog.search(module_name)
            try:
                app = context.registries.app_registry[match.lastindex - 1]
            except AttributeError:
                # TODO: Should we require apps?
                continue
            app.access.append(access)
            access.app = app

    def prepare_blueprint(self):
        # TODO: Should this go before prepare apps? Would love to
        # automatically get the app into the models etc.
        default_blueprint.run_hooks()

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

    def prepare_resolvers(self):
        pass

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
