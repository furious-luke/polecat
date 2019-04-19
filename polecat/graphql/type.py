from uuid import UUID

from graphql.error import INVALID
from graphql.language.ast import (BooleanValueNode, FloatValueNode,
                                  IntValueNode, StringValueNode)
from graphql.pyutils import inspect, is_finite, is_integer
from graphql.type.definition import GraphQLScalarType, is_named_type

__all__ = ('GraphQLDatetime',)


def serialize_datetime(value):
    if isinstance(value, str):
        # TODO: Confirm value is a datetime?
        return value
    if isinstance(value, datetime):
        # TODO: Which format?
        return str(value)
    # Do not serialize builtin types as strings, but allow
    # serialization of custom types via their `__str__` method.
    if type(value).__module__ == 'builtins':
        raise TypeError(f'Datetime cannot represent value: {inspect(value)}')
    return str(value)


def coerce_datetime(value):
    if not isinstance(value, str):
        raise TypeError(
            f'Datetime cannot represent a non string value: {inspect(value)}'
        )
    return value


def parse_datetime_literal(ast, _variables=None):
    """ Parse a string value node in the AST.
    """
    if isinstance(ast, StringValueNode):
        # TODO: Must be a datetime.
        return ast.value
    return INVALID


GraphQLDatetime = GraphQLScalarType(
    name="Datetime",
    description="The `Datetime` scalar type represents"
    " a date and time containing a timezone.",
    serialize=serialize_datetime,
    parse_value=coerce_datetime,
    parse_literal=parse_datetime_literal,
)


def serialize_uuid(value):
    if isinstance(value, str):
        # TODO: Confirm value is a UUID?
        return value
    if isinstance(value, UUID):
        # TODO: Which format?
        return str(value)
    # Do not serialize builtin types as strings, but allow
    # serialization of custom types via their `__str__` method.
    if type(value).__module__ == 'builtins':
        raise TypeError(f'UUID cannot represent value: {inspect(value)}')
    return str(value)


def coerce_uuid(value):
    if not isinstance(value, str):
        raise TypeError(
            f'UUID cannot represent a non string value: {inspect(value)}'
        )
    return value


def parse_uuid_literal(ast, _variables=None):
    """ Parse a string value node in the AST.
    """
    if isinstance(ast, StringValueNode):
        # TODO: Must be a UUID.
        return ast.value
    return INVALID


GraphQLUUID = GraphQLScalarType(
    name="UUID",
    description="The `UUID` scalar type represents"
    " a UUID.",
    serialize=serialize_uuid,
    parse_value=coerce_uuid,
    parse_literal=parse_uuid_literal,
)


# TODO: Prefer tuple, but we add it to a list in `./schema.py`.
scalars = [GraphQLDatetime, GraphQLUUID]
