from polecat.db.query.query import Values as QueryValues
from polecat.db.sql.expression import (LocalRole, LocalVariable, Multi, Select,
                                       Values)

from ..schema import create_table


def test_multipart_expression(immutabledb):
    table = create_table()
    expr = Multi(
        LocalRole('role'),
        LocalVariable('a', 1),
        Select(table, ('col1',))
    )
    sql = immutabledb.mogrify(*expr.to_sql())
    assert sql == (
        b'SET LOCAL ROLE "role"; SET LOCAL "a" TO 1; SELECT "a_table"."col1"'
        b' AS "col1" FROM "a_table"'
    )


def test_values_with_dict(immutabledb):
    expr = Values({
        'a': 1,
        'b': 2
    })
    sql = immutabledb.mogrify(*expr.to_sql())
    assert sql == b'VALUES (1, 2)'


def test_values_with_query_values(immutabledb):
    expr = Values(
        QueryValues({
            'a': 1,
            'b': 2
        })
    )
    sql = immutabledb.mogrify(*expr.to_sql())
    assert sql == b'VALUES (1, 2)'


def test_values_with_bulk_query_values(immutabledb):
    expr = Values(
        QueryValues(
            (
                (1, 2),
                (3, 4)
            ),
            ('a', 'b')
        )
    )
    sql = immutabledb.mogrify(*expr.to_sql())
    assert sql == b'VALUES (1, 2), (3, 4)'
