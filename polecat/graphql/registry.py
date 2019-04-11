# TODO: This registry is a bit awful. I probably need another
# abstraction from models -> types. The type would store the graphql
# type, create input, update input, etc. This way I can map from model
# to type, and then access the graphql type I need.

graphql_field_registry = {
}

graphql_type_registry = {
}

graphql_create_input_registry = {
}

graphql_update_input_registry = {
}

graphql_reverse_input_registry = {
}


class FieldMetaclass(type):
    def __init__(cls, name, bases, dct):
        if bases and name != 'Field':
            for src in getattr(cls, 'sources', ()):
                graphql_field_registry[src] = cls
        super().__init__(name, bases, dct)


def add_graphql_field_mapping(source, field_class):
    # TODO: Uniqueness
    graphql_field_registry[source] = field_class


def add_graphql_type(model, type):
    graphql_type_registry[model] = type


def add_graphql_create_input(model, type):
    graphql_create_input_registry[model] = type


def add_graphql_update_input(model, type):
    graphql_update_input_registry[model] = type
