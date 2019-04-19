from psycopg2.extensions import AsIs, adapt, register_adapter

__all__ = ('Point',)


class Point(object):
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)


def adapt_point(point):
    x = adapt(point.x).getquoted().decode()
    y = adapt(point.y).getquoted().decode()
    return AsIs("'(%s, %s)'" % (x, y))


register_adapter(Point, adapt_point)
