from polecat import model
from polecat.auth import jwt
from polecat.db.sql import Q


class AdminRole(model.Role):
    pass


class UserRole(model.Role):
    parents = (AdminRole,)


class DefaultRole(model.Role):
    parents = (UserRole,)


class JWTType(model.Type):
    token = model.TextField()


class User(model.Model):
    name = model.TextField()
    email = model.EmailField(unique=True, null=False)
    password = model.PasswordField()


class Address(model.Model):
    country = model.TextField()

    class Meta:
        access = model.Access(UserRole)


class Actor(model.Model):
    first_name = model.TextField()
    last_name = model.TextField()
    age = model.IntField()
    address = model.RelatedField(Address)

    class Meta:
        access = model.Access(
            all=UserRole,
            insert=DefaultRole,
            update=DefaultRole
        )


class Movie(model.Model):
    title = model.TextField()
    star = model.RelatedField(Actor)

    class Meta:
        access = model.Access(
            all=UserRole,
            select=DefaultRole
        )


class AuthenticateInput(model.Type):
    email = model.EmailField()
    password = model.PasswordField()

    class Meta:
        # TODO: Could actually ignore this, and then automatically
        # generate Input types when needed.
        input = True


class Authenticate(model.Mutation):
    input = AuthenticateInput
    returns = JWTType

    def resolve(self, email, password):
        result = (
            Q(User)
            .get(email=email, password=password)
            .select('id')
        )
        return {
            'token': jwt({'userId': result['id']})
        }
