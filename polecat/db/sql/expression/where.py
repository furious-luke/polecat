import re

import ujson
from psycopg2.sql import SQL, Composable, Identifier

from ....utils import to_tuple


class Where:
    FILTER_PROG = re.compile(r'^([a-zA-Z][a-zA-Z0-9_]+(?:__[a-zA-Z][a-zA-Z0-9_]+)*)$')
    FILTER_TYPES = None

    def __init__(self, *args, **kwargs):
        self.root = self.parse_input(args, kwargs)

    def get_sql(self, relation):
        self.relation = relation
        if self.root:
            return self.root.get_sql(self)
        else:
            return None

    def parse_input(self, args, kwargs):
        root = None
        for k, v in kwargs.items():
            m = self.FILTER_PROG.match(k)
            if not m:
                raise ValueError(f'Unable to match filter condition: {k}')
            target = m.group(1)
            lookup, flt_cls = self.parse_target(target)
            flt = flt_cls(self, lookup, v)
            if root is None:
                root = flt
            else:
                root = And(root, flt)
        for a in args:
            # TODO: Confirm that `a` is a proper FilterType.
            root = And(root, a)
        return root

    def parse_target(self, target):
        i = target.rfind('__')
        if i != -1:
            try:
                return target[:i], self.FILTER_TYPES[target[i + 2:]]
            except KeyError:
                pass
        return target, Equal

    def merge(self, other):
        # TODO: We should really do a check for duplicate filters.
        if self.root:
            if other.root:
                self.root = And(self.root, other.root)
        elif other.root:
            self.root = other.root

    def get_primary_columns(self):
        return self.root.get_primary_columns()


class FilterType:
    def __init__(self, filter, lookup, value):
        self.parse_lookup(lookup)
        self.parse_value(filter, value)

    def get_sql(self, filter):
        sql, args = self.eval(filter)
        sql = self.eval_joins(filter, sql)
        return sql, args

    def eval(self, filter):
        pass
        # val = self.value
        # if isinstance(self.value, str):
        #     val = val.format(**filter.context)
        # values.append(val)

    def eval_joins(self, filter, condition):
        if not self.joins:
            return condition
        sql = '%s'
        relation = filter.relation
        args = []
        for i, joined_column_name in enumerate(self.joins):
            # TODO: Handle m2m, reverse fk, reverse m2m.
            column = relation.get_column(joined_column_name)
            prev_tbl_name = relation.alias
            prev_col_name = column.name
            # TODO: Handle case of field not being related.
            relation = column.related_table
            tbl = relation.alias
            # TODO: Use Identifier
            # TODO: PK field other than 'id'.
            next = 'EXISTS (SELECT 1 FROM {} WHERE {} = {} AND %s)'
            args.extend([
                Identifier(tbl),
                SQL('{}.{}').format(Identifier(prev_tbl_name), Identifier(prev_col_name)),
                SQL('{}.id').format(Identifier(tbl))
            ])
            sql = sql % next
        sql = sql % '{}'
        args.append(condition)
        sql = SQL(sql).format(*args)
        return sql

    def parse_lookup(self, lookup):
        lookup_parts = lookup.split('__')
        if len(lookup_parts) < 1:
            raise ValueError(f'invalid filter: {lookup}')
        # if lookup_parts[-1] in Filter.FILTER_TYPES:
        #     self.type = lookup_parts.pop()
        # else:
        #     self.type = 'eq'
        self.joins = lookup_parts[:-1]
        self.field = lookup_parts[-1]

    def parse_value(self, filter, value):
        self.value = value

    def get_table_column(self, filter):
        relation = filter.relation
        table_name = relation.alias
        for joined_column_name in self.joins:
            column = relation.get_column(joined_column_name)
            relation = column.related_table
            table_name = relation.alias
        return table_name, self.field

    def format(self, format_string, *args):
        # TODO: A little ugly.
        if isinstance(self.value, Composable):
            format_string = format_string % '{}'
            return SQL(format_string).format(*(args + (self.value,))), ()
        else:
            return SQL(format_string).format(*args), to_tuple(self.value)

    def get_primary_columns(self):
        return (self.field,)


class Equal(FilterType):
    def eval(self, filter):
        super().eval(filter)
        try:
            tbl, col = self.get_table_column(filter)
        except KeyError:
            raise ValueError(f'invalid attribute: {self.field}')
        op = '=' if self.value is not None else 'IS'
        return self.format(
            '{}.{} {} %s',
            Identifier(tbl),
            Identifier(col),
            SQL(op)
        )


class NotEqual(FilterType):
    def eval(self, filter):
        super().eval(filter)
        try:
            tbl, col = self.get_table_column(filter)
        except KeyError:
            raise ValueError(f'invalid attribute: {self.field}')
        op = '!=' if self.value is not None else 'IS NOT'
        return self.format('{}.{} {} %s', tbl, col, op)


class Contains(FilterType):
    def eval(self, filter):
        super().eval(filter)
        try:
            tbl, col = self.get_table_column(filter)
        except KeyError:
            raise ValueError(f'invalid attribute: {self.field}')
        return self.format('{}.{} LIKE %s', tbl, col)

    def parse_value(self, filter, value):
        value = '%{}%'.format(value)
        self.value = value.replace('%', r'%%')


class Less(FilterType):
    def eval(self, filter):
        super().eval(filter)
        return self.format('{} < %s', self.field)


class Greater(FilterType):
    def eval(self, filter):
        super().eval(filter)
        return self.format('{} > %s', self.field)


class LessEqual(FilterType):
    def eval(self, filter):
        super().eval(filter)
        return self.format('{} <= %s', self.field)


class GreaterEqual(FilterType):
    def eval(self, filter):
        super().eval(filter)
        return self.format('{} >= %s', self.field)


class In(FilterType):
    def eval(self, filter):
        super().eval(filter)
        try:
            tbl, col = self.get_table_column(filter)
        except KeyError:
            raise ValueError(f'invalid attribute: {self.field}')
        return self.format('{}.{} = ANY (%s)', tbl, col)

    def parse_value(self, filter, value):
        try:
            self.value = ujson.loads(value)
        except Exception:
            raise ValueError(f'Unable to parse "in" filter value: {value}')


class NotIn(In):
    def eval(self, filter):
        FilterType.eval(self, filter)
        return self.format('{} NOT IN %s', self.field)


class IsNull(FilterType):
    def eval(self, filter):
        super().eval(filter)
        try:
            tbl, col = self.get_table_column(filter)
        except KeyError:
            raise ValueError(f'invalid attribute: {self.field}')
        op = 'IS' if self.value else 'IS NOT'
        return self.format('{}.{} {} NULL', tbl, col, op)

    def parse_value(self, filter, value):
        self.value = to_bool(value)


# class NotNull(FilterType):
#     def eval(self, filter):
#         super().eval(filter)
#         return f'{self.field} NOT NULL'


class Overlap(FilterType):
    def eval(self, filter):
        super().eval(filter)
        try:
            tbl, col = self.get_table_column(filter)
        except KeyError:
            raise ValueError(f'invalid attribute: {self.field}')
        return self.format('{}.{} && %s', tbl, col)


class WithinDistance(FilterType):
    def __init__(self, filter, lookup, point, distance):
        super().__init__(filter, lookup, distance)
        self.value = (point, self.value)

    def eval(self, filter):
        super().eval(filter)
        try:
            tbl, col = self.get_table_column(filter)
        except KeyError:
            raise ValueError(f'invalid attribute: {self.field}')
        return self.format('{}.{} <@> %s < %s', tbl, col)


class Operator:
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def get_sql(self, filter):
        raise NotImplementedError

    def eval_sides(self, filter):
        left_sql, left_args = self.left.get_sql(filter)
        right_sql, right_args = self.right.get_sql(filter)
        return left_sql, right_sql, left_args + right_args

    def get_primary_columns(self):
        return self.left.get_primary_columns() + self.right.get_primary_columns()


class And(Operator):
    def get_sql(self, filter):
        left, right, args = self.eval_sides(filter)
        # TODO: Making new SQLs here is probably a tiny bit inefficient.
        if isinstance(self.left, Or):
            left = SQL('({})').format(left)
        if isinstance(self.right, Or):
            right = SQL('({})').format(right)
        return SQL('{} AND {}').format(left, right), args


class Or(Operator):
    def get_sql(self, filter):
        left, right, args = self.eval_sides(filter)
        return SQL('{} OR {}').format(left, right), args


Where.FILTER_TYPES = {
    'eq': Equal,
    'ne': NotEqual,
    'lt': Less,
    'gt': Greater,
    'le': LessEqual,
    'ge': GreaterEqual,
    'in': In,
    'ct': Contains,
    'ni': NotIn,
    'nu': IsNull,
    # 'nn': NotNull,
    'ov': Overlap,
    # 'bt': Between
}
