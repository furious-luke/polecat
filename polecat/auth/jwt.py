from jwt import encode, decode
from polecat.core.config import default_config


def jwt(claims):
    return encode(
        claims or {},
        default_config.jwt_secret,
        algorithm='HS256'
    ).decode()


def jwt_decode(token):
    if isinstance(token, str):
        token = token.encode()
    return decode(
        token,
        default_config.jwt_secret,
        algorithms=('HS256',)
    )
