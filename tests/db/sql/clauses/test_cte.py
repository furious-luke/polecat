from unittest.mock import MagicMock

import pytest
from polecat.db.sql.expression.cte import CTE
from polecat.db.sql.expression.relation import Relation
from polecat.db.sql.sql import Sql

from .conftest import SqlTermTester


def test_append():
    term = CTE('test')
    term.append('cte0')
    term.append('cte1')
    sql = Sql(term.to_sql())
    assert str(sql) == 'WITH "c0" AS ("cte0"), "c1" AS ("cte1") "test"'


def test_prepend():
    term = CTE('test')
    term.prepend('cte0')
    term.prepend('cte1')
    sql = Sql(term.to_sql())
    assert str(sql) == 'WITH "c1" AS ("cte1"), "c0" AS ("cte0") "test"'


def test_to_sql():
    term = CTE('test')
    sql = Sql(term.to_sql())
    assert str(sql) == '"test"'


def test_recursive_expression():
    term = CTE('test')
    term.append('cte0').set_recursive_expression(Relation('rcrs'))
    sql = Sql(term.to_sql())
    assert str(sql) == 'WITH RECURSIVE "c0" AS ("cte0" UNION ALL "rcrs") "test"'


@pytest.mark.parametrize('test_func', SqlTermTester.ALL_TESTS)
def test_sql_term_methods(test_func):
    term = CTE(MagicMock())
    test_func(term)
