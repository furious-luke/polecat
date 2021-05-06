import pytest  # noqa
from polecat import model
from polecat.model.db import Q, Ref, S


class DummyModel(model.Model):
    n_related_dummies = model.QueryField(lambda: Q(RelatedDummyModel).filter(dummy=Ref('id')).count())
    max_timestamp = model.QueryField(lambda: Q(RelatedDummyModel).filter(dummy=Ref('id')).select('timestamp').max())


class RelatedDummyModel(model.Model):
    dummy = model.RelatedField(DummyModel, related_name='related_dummies')
    timestamp = model.DatetimeField()


def test_select_sql(db):
    # query = Q(DummyModel).select('id', 'n_related_dummies')
    query = Q(RelatedDummyModel).select('id', dummy=S('id', 'n_related_dummies', 'max_timestamp'))
    # print(list(query))
    print(query.to_sql())
