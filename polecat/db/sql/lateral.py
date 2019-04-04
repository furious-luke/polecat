from itertools import chain

from psycopg2.sql import SQL, Identifier


class LateralBackend:
    @classmethod
    def evaluate(cls, query):
        inner = (
            '{} {} {} {}'
            if query.parent
            else 'SELECT row_to_json(__tl) FROM ({} {} {} {}) AS __tl'
        )
        join_sql, join_args = cls.evaluate_all_join_clauses(query)
        where_sql, where_args = cls.evaluate_where_clause(query)
        return SQL(inner).format(
            cls.evaluate_select_clause(query),
            cls.evaluate_from_clause(query),
            join_sql,
            where_sql
        ), join_args + where_args

    @classmethod
    def evaluate_select_clause(cls, query):
        return SQL('SELECT {}').format(
            cls.evaluate_select_fields(query)
        )

    @classmethod
    def evaluate_select_fields(cls, query):
        return SQL(', ').join(chain(
            (
                SQL('{}.{}').format(
                    Identifier(query.table_alias),
                    Identifier(field_name)
                )
                for field_name in query.fields
            ),
            (
                SQL('row_to_json({}) AS {}').format(
                    Identifier(sub_query.join_alias),
                    Identifier(field_name)
                )
                for field_name, sub_query in query.lookups.items()
            )
        ))

    @classmethod
    def evaluate_from_clause(cls, query):
        sql = SQL('FROM {} AS {}').format(
            Identifier(query.model_class.Meta.table),
            Identifier(query.table_alias)
        )
        return sql

    @classmethod
    def evaluate_all_join_clauses(cls, query):
        # TODO: This doesn't seem very nice.
        sql, args = [], []
        for field_name, sub_query in query.lookups.items():
            result = cls.evaluate_join_clause(query, field_name, sub_query)
            sql.append(result[0])
            args.append(result[1])
        return SQL(' ').join(sql), sum(args, ())

    @classmethod
    def evaluate_join_clause(cls, query, field_name, sub_query):
        sub_sql, args = sub_query.evaluate()
        return SQL('LEFT JOIN LATERAL ({}) AS {} {}').format(
            sub_sql,
            Identifier(sub_query.join_alias),
            cls.evaluate_join_on_clause(query, field_name, sub_query)
        ), args

    @classmethod
    def evaluate_join_on_clause(cls, query, field_name, sub_query):
        return SQL('ON {}.{} = {}.{}').format(
            Identifier(sub_query.join_alias),
            Identifier('id'),
            Identifier(query.table_alias),
            Identifier(field_name)
        )

    @classmethod
    def evaluate_where_clause(cls, query):
        filter = query.filter
        if filter:
            sql, args = filter.get_sql(query.model_class, query.table_alias)
            # TODO: Filter should return its own SQL.
            return SQL('WHERE {}').format(SQL(sql)), args
        else:
            return SQL(''), ()
