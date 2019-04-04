graphql_field_registry = {
}

graphql_type_registry = {
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
