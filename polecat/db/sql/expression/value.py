from psycopg2.sql import SQL, Placeholder

from .expression import Expression


def value_to_sql(column, value):
    if isinstance(value, Expression):
        sql, args = value.to_sql()
        return SQL('{}').format(sql), args
    else:
        return Placeholder(), (column.to_db_value(value),)
