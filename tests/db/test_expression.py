from polecat.db.sql.expression import LocalRole, LocalVariable, Multi, Select

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
