from jwt import encode
from polecat.core.config import default_config


def jwt(claims):
    return encode(
        claims or {},
        default_config.jwt_secret,
        algorithm='HS256'
    ).decode()
