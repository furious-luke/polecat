from polecat.db.query.query import Values


def test_with_dict():
    values = {'a': 0, 'b': 1}
    query = Values(values)
    assert_values(query, values)


def test_with_tuples():
    columns = ('a', 'b')
    values = ((0, 1),)
    query = Values(values, columns)
    assert_values(query, dict(zip(columns, values[0])))


def test_iter_rows():
    columns = ('a', 'b')
    values = ((0, 1), (2, 3))
    query = Values(values, columns)
    rows = [list(r) for r in query.iter_rows()]
    assert rows == [[('a', 0), ('b', 1)], [('a', 2), ('b', 3)]]


def test_column_names():
    values = {'a': 0, 'b': 1}
    query = Values(values)
    columns = list(query.iter_column_names())
    assert columns == list(values.keys())


def test_is_bulk():
    columns = ('a', 'b')
    values = [(0, 1)]
    query = Values(values, columns)
    assert query.is_bulk() == False
    values.append((2, 3))
    query = Values(values, columns)
    assert query.is_bulk() == True


def assert_values(query, values):
    assert len(query.columns) == 2
    assert len(query.values) == 1
    assert len(query.values[0]) == 2
    for c, v in zip(query.columns, query.values[0]):
        assert v == values[c]
