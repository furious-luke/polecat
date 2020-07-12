import pytest
from polecat.db.sql.expression.alias import Alias
from polecat.db.sql.sql import Sql

from .conftest import SqlTermTester


def test_to_sql_with_no_column():
    alias = Alias('test')
    sql = Sql(alias.to_sql())
    assert str(sql) == '"test"'


def test_to_sql_with_column():
    alias = Alias('test', column='a')
    sql = Sql(alias.to_sql())
    assert str(sql) == '"test"."a"'


@pytest.mark.parametrize('test_func', SqlTermTester.ALL_TESTS)
def test_sql_term_methods(alias, test_func):
    test_func(alias)
