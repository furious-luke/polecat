from unittest.mock import MagicMock

import pytest
from polecat.db.sql.expression.array_agg import ArrayAgg
from polecat.db.sql.sql import Sql

from .conftest import SqlTermTester


def test_to_sql():
    term = ArrayAgg('test')
    sql = Sql(term.to_sql())
    assert str(sql) == 'array_agg("test")'


@pytest.mark.parametrize('test_func', SqlTermTester.ALL_TESTS)
def test_sql_term_methods(test_func):
    term = ArrayAgg(MagicMock())
    test_func(term)
