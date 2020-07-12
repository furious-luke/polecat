class SqlTerm:
    def get_column(self, name: str):
        return NotImplementedError

    def has_column(self, name: str) -> bool:
        return NotImplementedError

    def get_alias(self) -> str:
        raise NotImplementedError

    def get_root_relation(self) -> 'SqlTerm':
        raise NotImplementedError

    def get_subrelation(self, name: str) -> 'SqlTerm':
        raise NotImplementedError

    def push_selection(self, selection=None) -> None:
        pass
