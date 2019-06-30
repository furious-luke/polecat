from ...db.schema import Table
from ..field import MutableField
from .convert import convert_field


class TableBuilder:
    def build(self, model):
        return Table(
            model.Meta.table_name,
            columns=self.build_all_columns(model),
            app=model.Meta.app,
            uniques=model.Meta.uniques,
            checks=model.Meta.checks
        )

    def build_all_columns(self, model):
        columns = []
        for field in model.Meta.fields.values():
            if not isinstance(field, MutableField):
                continue
            columns.append(self.build_column(field))
        return columns

    def build_column(self, field):
        return convert_field(field)
