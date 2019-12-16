from psycopg2.sql import SQL, Identifier


class Policy:
    def __init__(self, name, expression):
        self.name = name.replace('.', '_')
        self.expression = expression

    def bind(self, table):
        self.table = table
        self.full_name = '{}_{}_pol'.format(
            self.table.name,
            self.name
        )

    @property
    def sql(self):
        sql = SQL('')
        if not self.table.is_rls_enabled():
            sql += SQL('ALTER TABLE {} ENABLE ROW LEVEL SECURITY; ').format(
                Identifier(self.table.name)
            )
        sql += SQL('CREATE POLICY {} ON {} USING ({})').format(
            Identifier(self.full_name),
            Identifier(self.table.name),
            SQL(self.expression)
        )
        return sql, ()

    def serialize(self):
        return 'policy.Policy(name={}, expression={})'.format(
            repr(self.name),
            repr(self.expression)
        )
