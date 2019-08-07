from .importing import import_attribute


class Proxy:
    def __init__(self, initfunc=None):
        self.__target = None
        self.__initfunc = initfunc

    def set_target(self, target):
        self.__target = target

    def get_target(self):
        return self.__target

    def __getattr__(self, name):
        if self.__target is None and self.__initfunc:
            self.__initfunc = import_attribute(self.__initfunc)
            self.__target = self.__initfunc()
        return getattr(self.__target, name)

    def __getitem__(self, *args, **kwargs):
        if self.__target is None and self.__initfunc:
            self.__initfunc = import_attribute(self.__initfunc)
            self.__target = self.__initfunc()
        return self.__target.__getitem__(*args, **kwargs)
