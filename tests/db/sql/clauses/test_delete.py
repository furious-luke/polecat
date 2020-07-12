from unittest.mock import MagicMock
from psycopg2.sql import Identifier

import pytest
from polecat.db.sql.expression.delete import Delete
from polecat.db.sql.sql import Sql

from .conftest import SqlTermTester


def test_to_sql():
    term = Delete('test')
    sql = Sql(term.to_sql())
    assert str(sql) == 'DELETE FROM "test"'


def test_with_returning():
    term = Delete('test', returning=('f0', 'f1'))
    sql = Sql(term.to_sql())
    assert str(sql) == 'DELETE FROM "test" RETURNING "f0", "f1"'


def test_with_where():
    where_mock = MagicMock()
    where_mock.get_sql.return_value = Identifier('f0'), ()
    term = Delete('test', where=where_mock)
    sql = Sql(term.to_sql())
    assert str(sql) == 'DELETE FROM "test" WHERE "f0"'


@pytest.mark.parametrize('test_func', SqlTermTester.ALL_TESTS - set((SqlTermTester.test_push_selection,)))
def test_sql_term_methods(test_func):
    term = Delete(MagicMock())
    test_func(term)


def test_push_selection():
    selection = 'test'
    term = Delete(MagicMock())
    term.push_selection(selection)
    term.term.push_selection.assert_not_called()
