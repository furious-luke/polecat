## Model ORM

Polecat provides a slightyly different interface for querying the
database directly from models. As with the DB ORM, the model layer
provides a query helper, `Q`. However with models, it may be called
with `Model` classes or instances as the first argument.

When a model instance is used as the first parameter, and a mutation
operation is being performed, the values contained on the model
instance are used instead of needing to be supplied as arguments. As
an example, consider the following:

```python
from polecat import model
from polecat.model.db import Q

class Movie(model.Model):
    title = model.TextField()

movie = Movie(title='Star Wars')

Q(movie).insert().execute()
```

The above inserts a movie with the title "Star Wars" directly from a
model instance.
