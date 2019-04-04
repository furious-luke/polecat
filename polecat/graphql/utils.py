from graphql.utilities.schema_printer import print_schema as schema_repr


def print_schema(schema):
    print(schema_repr(schema))
