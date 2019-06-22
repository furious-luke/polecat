import re

from jwt import decode

from ..core.context import active_context
from ..model.registry import role_registry

__all__ = ('JWTMiddleware', 'RoleMiddleware')


class JWTMiddleware:
    bearer_prog = re.compile(r'bearer\s+(\S+)', re.I)

    @active_context
    def run(self, event, context):
        claims = None
        jwt = event.request.headers.get('authorization', None)
        if jwt:
            match = self.bearer_prog.match(jwt)
            if match:
                jwt = match.group(1)
                claims = decode(
                    jwt,
                    context.config.jwt_secret,
                    algorithms=('HS256',)
                )
        event.claims = claims


class RoleMiddleware(JWTMiddleware):
    def __init__(self, default_role=None):
        super().__init__()
        self.default_role = default_role

    def run(self, event):
        super().run(event)
        role = self.default_role
        claims = event.claims
        if claims and 'role' in claims:
            # TODO: Inefficient. This can be rectified once I've
            # converted the model registries to actual registries.
            found = False
            for role_class in role_registry:
                if role_class.Meta.role == claims['role']:
                    found = True
                    role = role_class
                    break
            if not found:
                # TODO: Better exception.
                raise Exception('role not found')
        event.role = role
