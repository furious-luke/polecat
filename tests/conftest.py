import pytest
from polecat.db.connection import cursor
from polecat.db.migration import migrate
from polecat.db.utils import parse_url, push_database_url, unparse_url
from polecat.deploy.aws.server import LambdaServer
from polecat.deploy.server.server import Server
from polecat.test.factory import create_model_factory
from polecat.test.utils import environ
from polecat.utils import random_ident


@pytest.fixture(scope='session')
def testdb():
    dbinfo = parse_url()
    test_dbname = random_ident()
    with cursor() as curs:
        curs.execute(f'create database {test_dbname}')
    try:
        test_url = unparse_url({**dbinfo, 'dbname': test_dbname})
        with push_database_url(test_url):
            with cursor(test_url) as curs:
                yield curs
    finally:
        with cursor() as curs:
            curs.execute(f'drop database {test_dbname}')


@pytest.fixture(scope='session')
def migrateddb(testdb):
    migrate(cursor=testdb)
    yield testdb


@pytest.fixture
def db(migrateddb):
    url = migrateddb.connection.dsn
    dbinfo = parse_url(url)
    local_dbname = random_ident()
    migrateddb.execute(
        f'create database {local_dbname}'
        f' with template {dbinfo["dbname"]}'
    )
    try:
        local_url = unparse_url({**dbinfo, 'dbname': local_dbname})
        with push_database_url(local_url):
            with cursor() as curs:
                yield curs
    finally:
        with cursor() as curs:
            curs.execute(f'drop database {local_dbname}')


@pytest.fixture(scope='session')
def factory():
    return create_model_factory()


@pytest.fixture
def server():
    with environ(POLECAT_PROJECT='polecat.project.project.Project'):
        yield Server()


@pytest.fixture
def lambda_server():
    with environ(POLECAT_PROJECT='polecat.project.project.Project'):
        yield LambdaServer()
