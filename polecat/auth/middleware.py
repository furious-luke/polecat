import os
import re

from jwt import decode

from ..model.registry import role_registry
from ..project.exceptions import MissingConfigurationError

__all__ = ('JWTMiddleware', 'RoleMiddleware')


class JWTMiddleware:
    bearer_prog = re.compile(r'bearer\s+(\S+)', re.I)

    def run(self, event):
        claims = None
        jwt = event.request.headers.get('authorization', None)
        if jwt:
            match = self.bearer_prog.match(jwt)
            if match:
                jwt = match.group(1)
                try:
                    secret = os.environ['JWT_SECRET']
                except KeyError:
                    raise MissingConfigurationError('JWT_SECRET')
                claims = decode(jwt, secret, algorithms=('HS256',))
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
                raise Exception('fole not found')
        event.role = role
