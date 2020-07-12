from .relation import Relation


def to_clause(term):
    if term is None:
        return term
    if isinstance(term, str):
        return Relation(term)
    return term
