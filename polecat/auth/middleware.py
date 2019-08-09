import re

from jwt import decode
from polecat.core.config import default_config
from polecat.model import default_blueprint

__all__ = ('JWTMiddleware', 'RoleMiddleware')


class JWTMiddleware:
    bearer_prog = re.compile(r'bearer\s+(\S+)', re.I)

    def run(self, event):
        claims = None
        jwt = event.get_authorization_header()
        if jwt:
            match = self.bearer_prog.match(jwt)
            if match:
                jwt = match.group(1)
                claims = decode(
                    jwt,
                    default_config.jwt_secret,
                    algorithms=('HS256',)
                )
        event.claims = claims
        for key, value in (claims or {}).items():
            event.session.variables[f'claims.{key}'] = value


class RoleMiddleware(JWTMiddleware):
    def __init__(self, default_role=None):
        super().__init__()
        self.default_role = default_role

    def run(self, event):
        super().run(event)
        role = self.default_role
        claims = event.claims
        if claims and 'role' in claims:
            role = default_blueprint.roles[claims['role']]
        if role is None:
            # TODO: Better exception.
            raise Exception('No role specified')
        # TODO: Need both of these? Probs not.
        event.role = role
        event.session.role = role.Meta.dbrole if role else None
