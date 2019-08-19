from polecat.db.schema.variable import SessionVariable
from psycopg2.extensions import AsIs, adapt, register_adapter


def adapt_session_variable(sv):
    type = sv.type or ''
    if type:
        # TODO: Should be using a mapping from Python types to DB
        # types.
        type = f'::{type}'
    return AsIs(f"current_setting('{sv.name}', TRUE){type}")


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y


def adapt_point(point):
    # TODO: Would prefer not to have to decode.
    x = adapt(point.x).getquoted().decode()
    y = adapt(point.y).getquoted().decode()
    return AsIs("'(%s, %s)'" % (x, y))


register_adapter(Point, adapt_point)
register_adapter(SessionVariable, adapt_session_variable)
