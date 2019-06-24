# Polecat

A lean, powerful, and enjoyable web framework.

## Warning

This is *very* alpha software. It is not yet fully functional and will
certainly eat your cat.

## Features

 * Built-in high-performance ORM.
 * No `n + 1` query issues; a single SQL query is issued regardless of
   query depth.
 * Automatically produces GraphQL APIs (JSON-API specification is in
   the roadmap).
 * Includes (limited) built-in database migrations.
 * Testing facilities, including automatic model factories.
 
## Installation

Polecat comes as a PyPi package, and as such the easiest way to
install it is with `pip`:

``` bash
pip install polecat[cli]
```

The extras keyword `cli` indicates that the command line interface and
its dependencies should be installed. For production deployments those
dependencies are omitted.

## Documentation

Polecat's documentation can be found under the "docs" directory. At
the moment there are mostly guides to performing the most common
operations. Over time more guides and documentation will be added.

## Discussion

Django has always been one of my favorite web frameworks. The Django
community have absolutely hit the nail on the head for developer
experience. Python is fantastic to work with, and Django's
documentation is second to none. However, constructing
high-performance APIs can be a little tricky. There are plenty of
excellent libraries to leverage (Django Rest Framework, Graphene), but
there are also traps. The `n + 1` problem for example: one needs to be
sure to properly prefetch required data or performance will rapidly
degrade. I've always found this to be a frustrating experience,
GraphQL provides an interface to freely select nested relationships,
yet I need to curate each database query to ensure it's formulated
correctly, making the freedom provided by GraphQL moot.

Enter Postgraphile, a fantastic NodeJS library to automatically create
GraphQL APIs from a PostgreSQL database schema. Producing a typed,
`n + 1`-safe, API "free of charge" can be amazingly useful, especially
for all those typical CRUD operations needed. But no auto-generated
API is without the need for customisation. There are always unique
mutations and edge-cases. Postgraphile provides a number plugins which
ease the pain of extensions, but the developer experience begins to
suffer: there is no ORM available out of the box to assist in
performing database operations, and the documentation surrounding the
schema builder is a little scarce. Postgraphile encourages development
of customised queries using PostgreSQL's internal scripting
language(s). This works very well so long as you're able to write your
scripts without error. Debugging PostgreSQL functions can be a trying
experience, with unhelpful error messages and very limited ability for
stepping through your code. Again, developer experience suffers.

Polecat is inspired by both Django and Postgraphile. It borrows the
automatic creation of APIs from Postgraphile, and attempts to wrap it
in the same kind of convenience as Django. Polecat attempts to be
"batteries included", you should be able to use Polecat to build a
highly-performant, scalable API server, deployed to popular cloud
services, all the while enjoying a pleasant developer experience.

## Roadmap

Please visit the [development GitHub
project](https://github.com/furious-luke/polecat/projects/1) to see
upcoming work. If there's something on the roadmap you're keen to see
implemented, give the issue a thumbs up.

## Contributing

As with Django, Polecat is intended to be a free, community driven,
framework.
