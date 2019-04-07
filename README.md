# Polecat

A lean, powerful, and enjoyable web framework.

## Warning

This is *very* alpha software. It is not yet fully functional and will
certainly eat your cat.

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
for all those typical CRUD operations needed. But every API needs
customisation, unique mutations; various things to catch all those
edge-cases and perform atypical operations. Postgraphile provides a
number plugins which ease the pain of extensions, but the developer
experience begins to suffer: there is no ORM available out of the box
to assist in performing database operations, and the documentation
surrounding the schema builder is a little scarce. Postgraphile
encourages development of customised queries using PostgreSQL's
internal scripting language(s). This works very well so long as you're
able to write your scripts without error. Debugging PostgreSQL
functions can be a trying experience, with unhelpful error messages
and very limited ability for stepping through your code. Again,
developer experience suffers.

Polecat is inspired by both Django and Postgraphile. It incorporates
the automatic creation of APIs from Postgraphile, but wraps it in the
convenience of Django and Python. Polecat attempts to be "batteries
included", you should be able to use Polecat and only Polecat to build
a highly-performant, scalable API server, deployed to popular cloud
services, all the while enjoying a pleasant developer experience.

## Features

 * Built-in high-performance ORM.
 * No `n + 1` query issues.
 * Automatically produces JSON-API specification and GraphQL APIs.
 * Includes (limited) database migrations.
 * Testing facilities, including automatic model factories.

## Installation

Polecat comes as a PyPi package, and as such the easiest way to
install it is with `pip`:

``` bash
pip install polecat
```

## Getting Started

Getting started with Polecat is designed to be a trivial
excercise. Once installed, the `polecat` command should now be
accessible from your command line:

``` bash
polecat --help
```

Everything you'll need is available using the Polecat command. Let's
start by generating a basic "hello world" project.

``` bash
polecat example helloworld
```

The above command will create a `helloworld` folder in your current
directory, populated with a minimal project. Within, you'll find just
two files:

 * `models.py` - the data/API definition.
 * `project.py` - the entrypoint for your project.
 * `bundle.js` - the client side application.

To see your project working, from within the `helloworld` directory
run:

``` bash
polecat server
```

A local development server will be launched, navigate to
`http://localhost:8000` to see your new hello world project.

## Documentation

Please head over to the Wiki for more documentation.

## Contributing

As with Django, Polecat is intended to be a free, community driven,
framework.
