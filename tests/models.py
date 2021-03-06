from polecat import model
from polecat.auth import jwt
from polecat.db.schema.utils import Auto
from polecat.model.db import Q
from polecat.model.db.helpers import create_schema

# TODO: Convert this to use a function to generate the models to
# assist with easier testing?


class OverrideNameResolver:
    def build_model(self, context):
        model = context()
        model.name = 'override'
        return model


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
    created = model.DatetimeField(default=Auto)

    class Meta:
        app = type('App', (), {'name': 'auth'})


class Address(model.Model):
    country = model.TextField()


class AddressAccess(model.Access):
    entity = Address
    all = (UserRole,)


class Actor(model.Model):
    first_name = model.TextField()
    last_name = model.TextField()
    age = model.IntField(null=True)
    address = model.RelatedField(Address, null=True)
    user = model.RelatedField(User, null=True, default=model.session('claims.user_id', 'int'))

    class Meta:
        uniques = (
            ('first_name', 'last_name'),
        )
        checks = (
            'first_name is not null or last_name is not null',
        )


class ActorAccess(model.Access):
    entity = Actor
    all = (UserRole,)
    insert = (DefaultRole,)
    update = (DefaultRole,)


class Movie(model.Model):
    title = model.TextField(unique=True)
    star = model.RelatedField(Actor)


class MovieAccess(model.Access):
    entity = Movie
    all = (UserRole,)
    select = (DefaultRole,)


class Store(model.Model):
    name = model.TextField()
    parent = model.RelatedField('self')

    class Meta:
        mutation_resolvers = [
            OverrideNameResolver()
        ]


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
    route = 'authenticate'

    def resolve(self, ctx):
        input = ctx.parse_input()
        result = (
            Q(User)
            .filter(email=input['email'], password=input['password'])
            .select('id')
            .get()
        )
        return {
            'token': jwt({'userId': result['id']})
        }


schema = create_schema()
