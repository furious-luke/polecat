def passthrough(cls):
    """ Wrap another dictionary-like class to provide direct access to
    its contents through attribute access. The outer class is renamed
    to match the wrapped class, and the wrapped class is renamed to
    "Meta".
    """
    class Wrapper:
        def __init__(self, *args, **kwargs):
            self.__dict__['Meta'] = self.Meta(*args, **kwargs)

        def __getattr__(self, key):
            return self.Meta.get(key)

        def __setattr__(self, key, value):
            return self.Meta.set(key, value)

        def __getitem__(self, key):
            return self.Meta.get(key)

        def __setitem__(self, key, value):
            return self.Meta.set(key, value)

    Wrapper.__qualname__ = Wrapper.__name__ = cls.__name__
    cls.__qualname__ = cls.__name__ = 'Meta'
    Wrapper.Meta = cls
    return Wrapper


class PassthroughMetaclass:
    def __new__(meta, name, bases, attrs):
        cls = super().__new__(meta, name, bases, attrs)
        return passthrough(cls)
