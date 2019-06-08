def print_table(table):
    print(repr(table))
    for column in table.columns:
        print(f' {repr(column)}')
