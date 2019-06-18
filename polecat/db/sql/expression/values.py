from .expression import Expression


# TODO: Not sure I need this. Could be good though.
class Values(Expression):
    def to_sql(self):
        return SQL('VALUES ()')

    def get_values_sql_from_dict(self):
        column_names_sql = []
        column_values_sql = []
        column_values = []
        for column_name, column_value in self.values.items():
            column = self.relation.get_column(column_name)
            column_names_sql.append(Identifier(column_name))
            value_sql, value = value_to_sql(column, column_value)
            column_values_sql.append(value_sql)
            column_values.extend(value)
        return column_names_sql, column_values_sql, column_values
