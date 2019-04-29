import os

from jwt import encode

from ..project.exceptions import MissingConfigurationError


def jwt(claims):
    try:
        secret = os.environ['JWT_SECRET']
    except KeyError:
        raise MissingConfigurationError('JWT_SECRET')
    return encode(
        claims or {},
        secret,
        algorithm='HS256'
    ).decode()
