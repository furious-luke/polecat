from .model import Mutation


def create_mutation(name, resolver, returns=None, input=None):
    cls = type(name, (Mutation,), {
        'returns': returns,
        'input': input
    })
    cls.resolve = classmethod(resolver)
    return cls
