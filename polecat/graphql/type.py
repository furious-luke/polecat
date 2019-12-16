import ujson
from datetime import date, datetime
from uuid import UUID

from graphql.error import INVALID
from graphql.language.ast import (BooleanValueNode, FloatValueNode,
                                  IntValueNode, StringValueNode)
from graphql.pyutils import inspect, is_finite, is_integer
from graphql.type.definition import GraphQLScalarType, is_named_type

__all__ = ('GraphQLDatetime', 'GraphQLDate', 'GraphQLJSON')


def serialize_date(value):
    if isinstance(value, str):
        # TODO: Confirm value is a date?
        return value
    if isinstance(value, date):
        # TODO: Which format?
        return str(value)
    # Do not serialize builtin types as strings, but allow
    # serialization of custom types via their `__str__` method.
    if type(value).__module__ == 'builtins':
        raise TypeError(f'Date cannot represent value: {inspect(value)}')
    return str(value)


def coerce_date(value):
    if not isinstance(value, str):
        raise TypeError(
            f'Date cannot represent a non string value: {inspect(value)}'
        )
    return value


def parse_date_literal(ast, _variables=None):
    """ Parse a string value node in the AST.
    """
    if isinstance(ast, StringValueNode):
        # TODO: Must be a datetime.
        return ast.value
    return INVALID


GraphQLDate = GraphQLScalarType(
    name="Date",
    description="The `Date` scalar type represents"
    " a date.",
    serialize=serialize_date,
    parse_value=coerce_date,
    parse_literal=parse_date_literal
)


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


def serialize_json(value):
    return ujson.dumps(value)


def coerce_json(value):
    return ujson.loads(value)


def parse_json_literal(ast, _variables=None):
    """ Parse a string value node in the AST.
    """
    if isinstance(ast, StringValueNode):
        # TODO: Must be a UUID.
        return ast.value
    return INVALID


GraphQLJSON = GraphQLScalarType(
    name="JSON",
    description="The `JSON` scalar type represents"
    " a JSON.",
    serialize=serialize_json,
    parse_value=coerce_json,
    parse_literal=parse_json_literal,
)


# TODO: Prefer tuple, but we add it to a list in `./schema.py`.
scalars = [GraphQLDatetime, GraphQLUUID, GraphQLJSON]
