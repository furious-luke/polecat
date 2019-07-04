## Polecat ORM

The Polecat ORM is designed for both performance and ease of
use. Performance is achieved by allowing complex queries involving
both mutations and queries, to be carried out in a single SQL
query. This includes nested selections, the likes of which are
typically seen in GraphQL queries.

Technical complexity has been pushed downwards to the lowest
abstraction possible, removing the burden from the user at higher
abstractions.

The basic architecture of the ORM consistes of:

 * Query - how to represent the kind of query the end user is asking for.
 * Builder - helpers to assist in building a Query.
 * Expression - how to represent a query in a database appropriate way.
 * Strategy - various methods to translate a query to an expression.

### Query Cookbook

Let's start by assuming we have a few tables at our disposal:

```python
movies = Table('movie', columns=[
  IntColumn('id', primary_key=True),
  TextColumn('title', unique=True),
  IntColumn('year')
])

actors = Table('actor', columns=[
  IntColumn('id', primary_key=True),
  TextColumn('name')
])

roles = Table('role', columns=[
  IntColumn('id', primary_key=True),
  RelatedColumn('movie', related_table='movie', related_column='roles'),
  RelatedColumn('actor', related_table='actor', related_column='movies')
])
```

And we assume in all code examples the `Q` helper is available:

```python
from polecat.db import Q
```

Let's begin by selecting all available movies:

```python
all_movies = Q(movies).select().execute()
```

If you also need to iterate over your results, you may skip the `.execute()` method:

```python
for movie in Q(movies).select():
    pass
```
