class Lookup:
    separator = '__'

    def __init__(self, path):
        components = path.split('__')
        if len(components) > 1:
            self.branches = components[:-1]
            self.leaf = components[-1]
        else:
            self.branches = []
            self.leaf = path
