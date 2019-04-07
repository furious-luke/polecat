from itertools import chain

from psycopg2.sql import SQL, Identifier

# SELECT row_to_json(__tl)
#   FROM (
#     SELECT "t0"."first_name", "t0"."last_name", "t0"."id", "t0"."age", j1.array_agg AS "movies_by_star"
#       FROM "actor" AS "t0" LEFT JOIN LATERAL (
#         SELECT array_agg(j2) FROM (
#           SELECT "t1"."star", "t1"."id", "t1"."title" FROM "movie" AS "t1" WHERE "t1"."star" = "t0".id
#         ) AS j2
#       ) AS "j1" ON true
#   ) AS __tl;


class LateralBackend:
    @classmethod
    def evaluate(cls, query, extra_fields=None, extra_where=None):
        # TODO: This extra_fields and extra_where business is a bit ugly.
        inner = (
            '{} {} {} {}'
            if query.parent
            else 'SELECT row_to_json(__tl) FROM ({} {} {} {}) AS __tl'
        )
        join_sql, join_args = cls.evaluate_all_join_clauses(query)
        where_sql, where_args = cls.evaluate_where_clause(query, extra_where=extra_where)
        return SQL(inner).format(
            cls.evaluate_select_clause(query, extra_fields=extra_fields),
            cls.evaluate_from_clause(query),
            join_sql,
            where_sql
        ), join_args + where_args

    @classmethod
    def evaluate_select_clause(cls, query, extra_fields=None):
        return SQL('SELECT {}').format(
            cls.evaluate_select_fields(query, extra_fields)
        )

    @classmethod
    def evaluate_select_fields(cls, query, extra_fields=None):
        all_fields = query.fields
        if extra_fields:
            # TODO: Too much converting?
            all_fields = set(all_fields).union(set(extra_fields))
        return SQL(', ').join(chain(
            (
                SQL('{}.{}').format(
                    Identifier(query.table_alias),
                    Identifier(field_name)
                )
                for field_name in all_fields
            ),
            (
                SQL('{} AS {}').format(
                    SQL('{}.array_agg').format(Identifier(sub_query.join_alias))  # TODO: Oh my god no.
                    if query.model_class.Meta.fields[field_name].reverse
                    else Identifier(sub_query.join_alias),
                    Identifier(field_name)
                )
                for field_name, sub_query in query.lookups.items()
            )
        ))

    @classmethod
    def evaluate_from_clause(cls, query):
        table = 'cte_mut' if query.is_insert else query.model_class.Meta.table
        sql = SQL('FROM {} AS {}').format(
            Identifier(table),
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
        field = query.model_class.Meta.fields[field_name]
        if not field.reverse:
            sub_sql, args = sub_query.evaluate(extra_fields=('id',))
            return SQL('LEFT JOIN LATERAL ({}) AS {} {}').format(
                sub_sql,
                Identifier(sub_query.join_alias),
                cls.evaluate_join_on_clause(query, field_name, sub_query)
            ), args
        else:
            sub_sql, args = sub_query.evaluate(
                extra_fields=(field.related_name,),
                extra_where=SQL('{}.{} = {}.{}').format(
                    Identifier(sub_query.table_alias),
                    Identifier(field.related_name),
                    Identifier(query.table_alias),
                    Identifier('id')
                )
            )
            return SQL('LEFT JOIN LATERAL (SELECT array_agg({}) FROM({}) AS {}) AS {} {}').format(
                Identifier(sub_query.agg_alias),
                sub_sql,
                Identifier(sub_query.agg_alias),  # TODO: Duplicate (2-above).
                Identifier(sub_query.join_alias),
                cls.evaluate_join_on_clause(query, field_name, sub_query)
            ), args

    @classmethod
    def evaluate_join_on_clause(cls, query, field_name, sub_query):
        field = query.model_class.Meta.fields[field_name]
        if not field.reverse:
            return SQL('ON {}.{} = {}.{}').format(
                Identifier(sub_query.join_alias),
                Identifier('id'),
                Identifier(query.table_alias),
                Identifier(field_name)
            )
        else:
            return SQL('ON true')

    @classmethod
    def evaluate_where_clause(cls, query, extra_where=None):
        filter = query.filter
        if filter:
            sql, args = filter.get_sql(query.model_class, query.table_alias)
        else:
            sql, args = None, ()
        if extra_where:
            if sql:
                sql = SQL('({}) AND ({})').format(extra_where, sql)
            else:
                sql = extra_where
        if sql:
            return SQL('WHERE {}').format(sql), args
        else:
            return SQL(''), ()
