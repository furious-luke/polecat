import re

import ujson
from stdb.core.engine import default_engine as engine
from stdb.core.function import default_function_registry as function_registry
from stdb.utils import to_bool


class Filter:
    FILTER_PROG = re.compile(r'^([a-zA-Z]+(?:__[a-zA-Z]+)*)$')
    FILTER_TYPES = None

    def __init__(self, args):
        self.root = self.parse_args(args)

    def get_sql(self, version, endpoint):
        self.version = version
        self.endpoint = endpoint
        if self.root:
            return self.root.get_sql(self)
        else:
            return None

    def parse_args(self, args):
        root = None
        if args:
            for k, v in args.items():
                m = self.FILTER_PROG.match(k)
                if not m:
                    continue
                target = m.group(1)
                lookup, flt_cls = self.parse_target(target)
                flt = flt_cls(self, lookup, v)
                if root is None:
                    root = flt
                else:
                    root = And(root, flt)
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


class FilterType:
    def __init__(self, filter, lookup, value):
        self.parse_lookup(lookup)
        self.parse_value(filter, value)

    def get_sql(self, filter):
        sql = self.eval(filter)
        sql = self.eval_joins(filter, sql)
        return sql

    def eval(self, filter):
        pass
        # val = self.value
        # if isinstance(self.value, str):
        #     val = val.format(**filter.context)
        # values.append(val)

    def eval_joins(self, filter, condition):
        if not self.joins:
            return condition
        sql = '{next}'
        ep = filter.endpoint
        for j in self.joins:
            # TODO: Handle m2m, reverse fk, reverse m2m.
            prev_tbl = ep['table']
            prev_col = ep['fields'][j]['column']
            try:
                ep = filter.version[ep['fields'][j]['field']['other']]
            except KeyError:
                raise ValueError(f'invalid include during lookup: {j}')
            tbl = ep['table']
            next = 'EXISTS (SELECT 1 FROM %s WHERE %s = %s AND {next})' % (
                tbl,
                f'{prev_tbl}.{prev_col}',
                f'{tbl}.id'
            )
            sql = sql.format(next=next)
        sql = sql.format(next=condition)
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
        if isinstance(value, str) and len(value) and value[0] == '#':
            func = function_registry.parse(value[1:])
            value = func()
        self.value = engine.quote_literal(value)

    def get_table_column(self, filter):
        ep = filter.endpoint
        for j in self.joins:
            try:
                ep = filter.version[ep['fields'][j]['field']['other']]
            except KeyError:
                raise ValueError(f'invalid include during lookup: {j}')
        if self.field == 'id':
            return ep['table'], 'id'
        else:
            try:
                return ep['table'], ep['fields'][self.field]['column']
            except KeyError:
                raise ValueError(f'invalid field during lookup: {self.field}')


class Equal(FilterType):
    def eval(self, filter):
        super().eval(filter)
        try:
            tbl, col = self.get_table_column(filter)
        except KeyError:
            raise ValueError(f'invalid attribute: {self.field}')
        op = '=' if self.value is not None else 'IS'
        return f'{tbl}.{col} {op} %s' % self.value


class NotEqual(FilterType):
    def eval(self, filter):
        super().eval(filter)
        try:
            tbl, col = self.get_table_column(filter)
        except KeyError:
            raise ValueError(f'invalid attribute: {self.field}')
        op = '!=' if self.value is not None else 'IS NOT'
        return f'{tbl}.{col} {op} %s' % self.value


class Contains(FilterType):
    def eval(self, filter):
        super().eval(filter)
        try:
            tbl, col = self.get_table_column(filter)
        except KeyError:
            raise ValueError(f'invalid attribute: {self.field}')
        return f'{tbl}.{col} LIKE %s' % self.value

    def parse_value(self, filter, value):
        value = '%{}%'.format(value)
        self.value = engine.quote_literal(value.replace('%', r'%%'))


class Less(FilterType):
    def eval(self, filter):
        super().eval(filter)
        return f'{self.field} < %s' % self.value


class Greater(FilterType):
    def eval(self, filter):
        super().eval(filter)
        return f'{self.field} > %s' % self.value


class LessEqual(FilterType):
    def eval(self, filter):
        super().eval(filter)
        return f'{self.field} <= %s' % self.value


class GreaterEqual(FilterType):
    def eval(self, filter):
        super().eval(filter)
        return f'{self.field} >= %s' % self.value


class In(FilterType):
    def eval(self, filter):
        super().eval(filter)
        try:
            tbl, col = self.get_table_column(filter)
        except KeyError:
            raise ValueError(f'invalid attribute: {self.field}')
        return f'{tbl}.{col} = ANY (%s)' % self.value

    def parse_value(self, filter, value):
        try:
            self.value = engine.quote_array(ujson.loads(value))
        except Exception:
            raise ValueError(f'Unable to parse "in" filter value: {value}')


class NotIn(In):
    def eval(self, filter):
        FilterType.eval(self, filter)
        return f'{self.field} NOT IN %s' % self.value


class IsNull(FilterType):
    def eval(self, filter):
        super().eval(filter)
        try:
            tbl, col = self.get_table_column(filter)
        except KeyError:
            raise ValueError(f'invalid attribute: {self.field}')
        op = 'IS' if self.value else 'IS NOT'
        return f'{tbl}.{col} {op} NULL'

    def parse_value(self, filter, value):
        self.value = to_bool(value)


class NotNull(FilterType):
    def eval(self, filter):
        super().eval(filter)
        return f'{self.field} NOTNULL'


class Overlap(FilterType):
    def eval(self, filter):
        super().eval(filter)
        try:
            tbl, col = self.get_table_column(filter)
        except KeyError:
            raise ValueError(f'invalid attribute: {self.field}')
        return f'{tbl}.{col} && {self.value}'


class Operator:
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def get_sql(self, filter):
        raise NotImplementedError

    def eval_sides(self, filter):
        left = self.left.get_sql(filter)
        right = self.right.get_sql(filter)
        return left, right


class And(Operator):
    def get_sql(self, filter):
        left, right = self.eval_sides(filter)
        if isinstance(self.left, Or):
            left = f'({left})'
        if isinstance(self.right, Or):
            right = f'({right})'
        return f'{left} AND {right}'


class Or(Operator):
    def get_sql(self, filter):
        left, right = self.eval_sides(filter)
        return f'{left} OR {right}'


Filter.FILTER_TYPES = {
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
    'nn': NotNull,
    'ov': Overlap,
    # 'bt': Between
}
