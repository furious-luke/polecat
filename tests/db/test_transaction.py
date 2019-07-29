from polecat.db.connection import transaction
from polecat.model.db import Q

from ..models import Movie


def test_transaction(migrateddb, factory):
    n_movies_pre = len(list(Q(Movie).select()))
    try:
        with transaction():
            factory.Movie()
            raise Exception
    except Exception:
        pass
    n_movies_post = len(list(Q(Movie).select()))
    assert n_movies_pre == n_movies_post
