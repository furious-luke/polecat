from ...db.schema import Table
from ..field import MutableField
from .convert import convert_field


class TableBuilder:
    def __init__(self):
        self.processing_models = set()

    def build(self, model):
        if model in self.processing_models:
            # TODO: This is to catch self-referential
            # models. Returning the name means the DB schema can bind
            # it later. Refactor for clarity.
            table_name = f'{model.Meta.table_name}'
            if model.Meta.app:
                # TODO: Also pretty horrible.
                table_name = f'{model.Meta.app.name.lower()}_{table_name}'
            return table_name
        table = getattr(model.Meta, 'table', None)
        if not table:
            self.processing_models.add(model)
            table = self.build_table(model)
            self.processing_models.remove(model)
            model.Meta.table = table
        return table

    def build_table(self, model):
        return Table(
            model.Meta.table_name,
            columns=self.build_all_columns(model),
            app=model.Meta.app,
            uniques=model.Meta.uniques,
            checks=model.Meta.checks,
            indexes=model.Meta.indexes
        )

    def build_all_columns(self, model):
        columns = []
        for field in model.Meta.fields.values():
            if not isinstance(field, MutableField):
                continue
            columns.append(self.build_column(field))
        return columns

    def build_column(self, field):
        return convert_field(field, self)
