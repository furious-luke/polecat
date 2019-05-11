from jwt import encode

from ..core.context import active_context


@active_context
def jwt(claims, context):
    return encode(
        claims or {},
        context.config.jwt_secret,
        algorithm='HS256'
    ).decode()
