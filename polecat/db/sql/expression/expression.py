from ..sql_term import SqlTerm

from .utils import to_clause


# TODO: Rename to Clause.
class Expression(SqlTerm):
    # TODO: term shouldn't be optional.
    def __init__(self, term=None):
        self.term = to_clause(term)

    def get_alias(self) -> str:
        return self.term.get_alias()

    def get_subrelation(self, name):
        return self.term.get_subrelation(name)

    def get_column(self, name):
        return self.term.get_column(name)

    def has_column(self, name):
        return self.term.has_column(name)

    def push_selection(self, selection=None):
        self.term.push_selection(selection)
