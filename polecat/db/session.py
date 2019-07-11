class Session:
    def __init__(self, role=None, variables=None):
        self.role = role
        self.variables = variables or {}

    def is_empty(self):
        return not self.role and not self.variables
