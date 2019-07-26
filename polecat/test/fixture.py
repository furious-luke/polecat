from contextlib import contextmanager

from polecat.db.connection import cursor, manager
from polecat.db.query.selection import Selection
from polecat.db.session import Session
from polecat.db.utils import unparse_url
from polecat.model.db.migrate import sync
from polecat.model.resolver import APIContext
from polecat.project.project import load_project
from polecat.test.factory import create_model_factory
from polecat.utils import random_ident

from .utils import create_database

__all__ = ('server', 'immutabledb', 'testdb', 'migrateddb', 'db', 'factory')


class ServerFixture:
    def __init__(self):
        self.project = load_project()
        self.project.prepare()

    def all_query(self, model_class, **kwargs):
        model_class = self.get_model_class(model_class)
        api_context = self.build_api_context(model_class, **kwargs)
        return model_class.Meta.all_resolver_manager(api_context)

    def get_query(self, model_class, id, **kwargs):
        model_class = self.get_model_class(model_class)
        api_context = self.build_api_context(
            model_class,
            arguments={
                'id': id
            },
            **kwargs
        )
        return model_class.Meta.all_resolver_manager(api_context)

    def create_mutation(self, model_class, input, **kwargs):
        model_class = self.get_model_class(model_class)
        api_context = self.build_api_context(
            model_class,
            input=input,
            **kwargs
        )
        return model_class.Meta.create_resolver_manager(api_context)

    def update_mutation(self, model_class, id, input, **kwargs):
        model_class = self.get_model_class(model_class)
        api_context = self.build_api_context(
            model_class,
            arguments={
                'id': id
            },
            input=input,
            **kwargs
        )
        return model_class.Meta.create_resolver_manager(api_context)

    def delete_mutation(self, model_class, id, **kwargs):
        model_class = self.get_model_class(model_class)
        api_context = self.build_api_context(
            model_class,
            input={
                'id': id
            },
            **kwargs
        )
        return model_class.Meta.delete_resolver_manager(api_context)

    def build_api_context(self, model_class=None, arguments=None, input=None,
                          role=None):
        return TestAPIContext(
            model_class,
            arguments=arguments,
            input=input,
            role=role or self.project.default_role
        )

    def get_model_class(self, model_class):
        if isinstance(model_class, str):
            return self.project.models[model_class]
        else:
            return model_class


class TestAPIContext(APIContext):
    def __init__(self, model_class=None, arguments=None, input=None,
                 role=None):
        super().__init__()
        self._model_class = model_class
        self._arguments = arguments or {}
        self._input = input or {}
        self.session = Session(role=role)
        self.event = type('TestEvent', (), {
            'role': role,
            'session': self.session
        })

    @property
    def model_class(self):
        return self._model_class

    def parse_argument(self, name):
        return self._arguments.get(name)

    def parse_input(self):
        return self._input

    def raw_input(self):
        return self._input

    def get_selector(self):
        return Selection()


@contextmanager
def server():
    yield ServerFixture()


@contextmanager
def immutabledb():
    with cursor() as curs:
        yield curs


@contextmanager
def testdb():
    with create_database() as curs:
        yield curs


@contextmanager
def migrateddb():
    # Should be scoped to the session.
    try:
        # Loading the project ensures we have all models.
        load_project()
        # TODO: Catch better error.
    except Exception:
        pass
    with create_database() as curs:
        sync(cursor=curs)
        yield curs


@contextmanager
def db(migrateddb):
    url = migrateddb.connection.dsn
    dbinfo = manager.parse_url(url)
    local_dbname = random_ident()
    migrateddb.execute(
        f'create database {local_dbname}'
        f' with template {dbinfo["dbname"]}'
    )
    try:
        local_url = unparse_url({**dbinfo, 'dbname': local_dbname})
        with manager.push_url(local_url):
            with cursor() as curs:
                yield curs
    finally:
        with cursor() as curs:
            curs.execute(f'drop database {local_dbname}')


@contextmanager
def factory():
    # Should be scoped to the session.
    yield create_model_factory()
