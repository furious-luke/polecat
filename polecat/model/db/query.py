from polecat.db.query import Q as BaseQ
from polecat.db.query import S

from ..model import Model
from .helpers import model_to_table, model_to_values, set_values_on_model

__all__ = ('Q', 'S')


class Q(BaseQ):
    def __init__(self, model, queryable=None, branches=None, session=None):
        super().__init__(
            queryable or model_to_table(model),
            branches,
            session
        )
        self.model = model

    def insert(self, model_or_subquery=None, **kwargs):
        if isinstance(model_or_subquery, Model):
            if kwargs:
                raise ValueError('Cannot pass both model and values to insert')
            return self.insert_from_model_argument(model_or_subquery)
        elif not kwargs and isinstance(self.model, Model):
            # TODO: Ensure test for this.
            # if not isinstance(self.model, Model):
            #     raise ValueError(
            #         'Cannot pass nothing to insert when root queryable is not'
            #         ' a Model'
            #     )
            return self.insert_from_root()
        else:
            return super().insert(**kwargs)

    def insert_from_model_argument(self, model):
        return super().insert(**model_to_values(model))

    def insert_from_root(self):
        return super().insert(**model_to_values(self.model))

    def update(self, model_or_subquery=None, **kwargs):
        if isinstance(model_or_subquery, Model):
            if kwargs:
                raise ValueError('Cannot pass both model and values to update')
            return self.update_from_model_argument(model_or_subquery)
        elif not kwargs:
            if not isinstance(self.model, Model):
                raise ValueError(
                    'Cannot pass nothing to update when root queryable is not'
                    ' a Model'
                )
            return self.update_from_root()
        else:
            return super().update(**kwargs)

    def update_from_model_argument(self, model):
        id = self.get_model_id(model)
        return (
            super()
            .filter(id=id)
            .update(**model_to_values(model, exclude_fields=('id',)))
        )

    def update_from_root(self):
        id = self.get_model_id(self.model)
        return (
            super()
            .filter(id=id)
            .update(**model_to_values(self.model, exclude_fields=('id',)))
        )

    def get_model_id(self, model):
        id = getattr(model, 'id', None)
        if id is None:
            raise ValueError('Model has no ID set.')
        return id

    def into(self, destination_model):
        for row in self:
            set_values_on_model(row, destination_model)
            return destination_model
        raise ValueError('No results returned from query')

    def chain(self, queryable):
        return self.__class__(self.model, queryable, self.branches, self.session)
