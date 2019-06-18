from .as_ import As
from .expression import Expression
from .select import Select
from .subquery import Subquery
from .union import Union


class SubrelationOverride(Expression):
    # TODO: Uh oh.
    override_counter = 0

    def __init__(self, expression, overrides, root_strategy):
        self.expression = expression
        self.overrides = overrides
        # TODO: This isn't nice.
        self.root_strategy = root_strategy

    def to_sql(self):
        return self.expression.to_sql()

    def get_subrelation(self, name):
        if name in self.overrides:
            override_queries = self.overrides[name]
            if len(override_queries) > 1:
                union = Union()
                for query in override_queries:
                    # TODO: What if it doesn't exist?
                    alias = self.root_strategy.get_query_alias(query)
                    union.add_expression(Select(alias))
                return As(Subquery(union), self.create_alias_name_for_override())
            else:
                return self.root_strategy.get_query_alias(override_queries[0])
        else:
            return self.expression.get_subrelation(name)

    def get_column(self, name):
        # TODO: Also bad design, but also what's the difference
        # between this and the above? Looks like the above just does
        # 'this.related_table'.
        return self.expression.get_column(name)

    def has_column(self, name):
        # TODO: Also bad design, but also what's the difference
        # between this and the above? Looks like the above just does
        # 'this.related_table'.
        return self.expression.has_column(name)

    def push_selection(self, selection=None):
        self.expression.push_selection(selection)

    def create_alias_name_for_override(self):
        alias_name = f'o{self.override_counter}'
        self.override_counter += 1
        return alias_name
