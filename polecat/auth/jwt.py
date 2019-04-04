import os

from jwt import encode


def jwt(claims):
    return encode(
        claims or {},
        os.environ['JWT_SECRET'],
        algorithm='HS256'
    ).decode()
