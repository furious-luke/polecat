from polecat import model
from polecat.model.resolver import Resolver


class TestResolver1(Resolver):
    pass


class TestResolver2(Resolver):
    pass


class ModelResolverTestModel(model.Model):
    col1 = model.TextField()

    class Meta:
        mutation_resolver = TestResolver1()


class ModelResolverTest(model.ModelResolver):
    model_class = ModelResolverTestModel

    class MutationResolver(Resolver):
        pass


def test_chaining():
    mutation_resolvers = ModelResolverTestModel.Meta.mutation_resolver
    assert isinstance(mutation_resolvers[0], ModelResolverTest.MutationResolver)
    assert isinstance(mutation_resolvers[1], TestResolver1)
