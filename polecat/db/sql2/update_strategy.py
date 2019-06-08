from .expression.update import Update
from .insert_strategy import InsertStrategy


class UpdateStrategy(InsertStrategy):
    def parse_query(self, query):
        return Update(
            query.source,
            self.parse_values_or_subquery(query.values),
            returning=self.root.current_select_columns
        )
