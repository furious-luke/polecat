from polecat.model.resolver import APIContext, ResolverManager


def resolver_0(context):
    context.called.append(resolver_0)
    return context()


def resolver_1(context):
    context.called.append(resolver_1)
    return 'result'


def build_resolver_manager():
    class TestResolverManager(ResolverManager):
        def iter_resolvers(self, context):
            yield resolver_0
            yield resolver_1
    return TestResolverManager()


def build_api_context():
    class TestAPIContext(APIContext):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.called = []
    return TestAPIContext()


def test_multiple_function_resolvers():
    manager = build_resolver_manager()
    api_ctx = build_api_context()
    result = manager.resolve(api_ctx)
    assert result == 'result'
    assert api_ctx.called == [resolver_0, resolver_1]
