from polecat import model
from polecat.auth import jwt
from polecat.db.sql import Q
from polecat.project import Project


class DefaultRole(model.Role):
    pass


class User(model.Model):
    name = model.TextField()
    email = model.EmailField(unique=True, null=False)
    password = model.PasswordField()


class JWTType(model.Type):
    token = model.TextField()


class Authenticate(model.Mutation):
    returns = JWTType

    def resolve(self, email, password):
        result = Q(User).get(email=email, password=password).select('id')
        return jwt({'userId': result['id']})


class AuthExample(Project):
    default_role = DefaultRole
