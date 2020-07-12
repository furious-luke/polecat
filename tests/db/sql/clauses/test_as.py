from unittest.mock import MagicMock

import pytest
from polecat.db.sql.expression.as_ import As
from polecat.db.sql.sql import Sql

from .conftest import SqlTermTester


def test_to_sql():
    term = As('test', 'a0')
    sql = Sql(term.to_sql())
    assert str(sql) == '"test" AS "a0"'


def test_nested_expression():
    term = As(As('test', 'a0'), 'a1')
    sql = Sql(term.to_sql())
    assert str(sql) == '"test" AS "a0" AS "a1"'


@pytest.mark.parametrize('test_func', SqlTermTester.ALL_TESTS)
def test_sql_term_methods(test_func):
    term = As(MagicMock(), 'a0')
    test_func(term)
