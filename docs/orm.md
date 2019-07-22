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

 * Query - how to represent the kind of query the end user is asking
   for.
 * Builder - helpers to assist in building a Query.
 * Expression - how to represent a query in a database appropriate
   way.
 * Strategy - various methods to translate a query to an expression.
 
 ---
 **NOTE**
 
 This section details how to use the ORM in isolation of the "model"
 subsystem. More often than not, models are the abstraction at which
 queries will be carried out. While very similar to using the ORM at
 the "db" layer, there are some subtle differences. Please refer to
 the [model documentation](model-orm.md) for details.
 
 ---

### Query Cookbook

Let's start by assuming we have a few tables at our disposal:

```python
movies = Table('movie', columns=[
  IntColumn('id', primary_key=True),
  TextColumn('title', unique=True),
  IntColumn('year'),
  IntColumn('rating')
])

actors = Table('actor', columns=[
  IntColumn('id', primary_key=True),
  TextColumn('name')
])

roles = Table('role', columns=[
  IntColumn('id', primary_key=True),
  TextColumn('character'),
  RelatedColumn('movie', related_table='movie', related_column='roles'),
  RelatedColumn('actor', related_table='actor', related_column='movies')
])
```

And we assume in all code examples the `Q` helper is available:

```python
from polecat.db import Q
```

#### Basic Queries

Let's begin by selecting all available movies:

```python
all_movies = list(Q(movies).select())
```

If you would prefer to iterate over your results as a generator:

```python
for movie in Q(movies).select():
    pass
```

To filter for all movies created in 1990, and to select only the name:

```python
filtered_movies = (
    Q(movies)
    .filter(year=1990)
    .select('name')
)
```

If you expect there to be only one result for your query, you may
"get" the record with:

```python
movie = (
    Q(movies)
    .filter(id=1)
    .get()
)
```

#### Nested Queries

Often queries need to span nested relationships. This is particularly
true in GraphQL APIs, and can have an enormous impact on performance.
The Polecat ORM makes nested queries trivial. To select all movies,
the roles, and the actors who played those roles:

```python
from polecat.db import S

data = Q(movies).select(
    'title',
    roles=S(
        'character',
        actor=S(
            'name'
        )
    )
)
```

Using the selection operator, `S`, one can select the specific nested
fields, returning only what is required. Behind the scenes the ORM
constructs an efficient SQL query to carry out the selection in one
round trip to the database.

#### Basic Mutations

To insert a movie:

```python
query = (
    Q(movies)
    .insert(name='Star Wars')
    .execute()
)
```

Note the use of `execute`. In this instance, as we are not returning
any selections from the query, to actually carry out the operation we
must call execute. If, however, we were returning a selection `get`
could be used:

```python
new_movie = (
    Q(movies)
    .insert(name='Star Wars')
    .get()
)
```

For the remaining examples we will omit the call to execute.

To update a single movie, use a filter in combination with the
`update` mutation:

```python
query = (
    Q(movies)
    .filter(id=1)
    .update(name='Star Wars')
)
```

Often multiple entries need to be updated, in which case relax the
conditions supplied to the filter:

```python
query = (
    Q(movies)
    .filter(year=1990)
    .update(rating=10)
)
```

Deletes work similarly to updates with regard to filtering. Perhaps
we've decided we don't like any of the movies from the 80s:

```python
query = (
    Q(movies)
    .filter(year__ge=1980, year__lt=1990)
    .delete()
)
```

#### Branching

The Polecat ORM allows multiple unrelated (or related) queries to be
carried out simultaneously. This is referred to as query branching,
and most of the time it will occur in the background without needing
to worry. For example, consider a sequence of multiple insertions:

```python
query = (
    Q(movies)
    .insert(name='Star Wars: A New Hope')
    .insert(name='Star Wars: The Empire Strikes Back')
    .insert(name='Star Wars: Return of the Jedi')
)
```

This results in three different SQL insertions, combined together into
a single query using implicit branching.

Sometimes you may wish to be more explicit with branching in order to
use more complex queries. For example, I may wish to update a
particular actor, and also insert a new movie:

```python
query = (
    Q(actors)
    .filter(id=1)
    .update(name='Mark Hamill')
    .branch(
        Q(movies)
        .insert(name='Star Wars')
    )
)
```

Again, this query would be sent to the database as a single SQL
operation.

#### Subqueries

Branching provides a mechanism for performing numerous unrelated
operations, however often we want to perform operations that are
somehow connected to one-another. For example, to insert an actor, a
role for that actor, and the movie in which the role occurs, all at
the same time:

```python
query = (
    Q(roles)
    .insert(
        character='Luke Skywalker',
        actor=(
            Q(actors)
            .insert(name='Mark Hamill')
            .select('id')
        ),
        movie=(
            Q(movies)
            .insert(name='Star Wars')
            .select('id')
        )
    )
)
```
