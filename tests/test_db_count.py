import pytest  # noqa
from polecat import model
from polecat.model.db import Q, Count


class DummyModel(model.Model):
    value = model.TextField()


def test_select_sql(db):
    query = Q(DummyModel).select(Count('*', 'n_dummies'))
    # print(query.to_sql())
