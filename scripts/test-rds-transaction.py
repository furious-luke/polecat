from polecat.db.connection import cursor, manager, transaction


class Rollback(Exception):
    pass


def check_row_count(version):
    with cursor() as curs:
        curs.execute('SELECT * FROM test_table;')
        all_results = list(curs)
        if len(all_results):
            print(f'Failed for {version}: {len(all_results)} results')
        else:
            print(f'Succeeded for {version}')


with cursor() as curs:
    curs.execute(
        'CREATE TABLE IF NOT EXISTS test_table(id serial primary key, value int);'
    )

try:
    with cursor(autocommit=True) as curs:
        with transaction():
            curs.execute('INSERT INTO test_table (value) VALUES (1);')
            curs.execute('INSERT INTO test_table (value) VALUES (2);')
            raise Rollback
except Rollback:
    pass
check_row_count('autocommit=True')
manager.close_all_connections()

try:
    with cursor(autocommit=False) as curs:
        with transaction():
            curs.execute('INSERT INTO test_table (value) VALUES (1);')
            curs.execute('INSERT INTO test_table (value) VALUES (2);')
            raise Rollback
except Rollback:
    pass
check_row_count('autocommit=False')
manager.close_all_connections()

try:
    with cursor(autocommit=True) as curs:
        with transaction():
            curs.execute('INSERT INTO test_table (value) VALUES (1);')
            curs.connection.commit()
            curs.execute('INSERT INTO test_table (value) VALUES (2);')
            raise Rollback
except Rollback:
    pass
check_row_count('autocommit=True & commit')
manager.close_all_connections()

try:
    with cursor(autocommit=False) as curs:
        with transaction():
            curs.execute('INSERT INTO test_table (value) VALUES (1);')
            curs.connection.commit()
            curs.execute('INSERT INTO test_table (value) VALUES (2);')
            raise Rollback
except Rollback:
    pass
check_row_count('autocommit=False & commit')
manager.close_all_connections()

with cursor() as curs:
    curs.execute('DELETE FROM test_table;')
    curs.execute('DROP TABLE test_table;')
