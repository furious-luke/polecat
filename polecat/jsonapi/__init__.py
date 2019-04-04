from stdb.core.auth import check_access
from stdb.core.cache import default_cache as cache
from stdb.exceptions import StdbError
from stdb.utils import split_handle

from .bulk_create import BulkCreate
from .bulk_update import BulkUpdate
from .create import Create
from .delete import Delete
from .detail import Detail
from .filter import Filter
from .multi.list import List
from .update import Update


class DoesNotExist(Exception):
    pass


def create(handle, data, id=None):
    ver, ep = cache.get_version_and_endpoint(handle)
    check_access(ep, 'create')
    if id is None:
        qry = Create(ver, ep, data)
    else:
        qry = Update(ver, ep, id, data)
    return qry.execute()


def update(handle, id, data):
    ver, ep = cache.get_version_and_endpoint(handle)
    check_access(ep, 'update')
    qry = Update(ver, ep, id, data)
    return qry.execute()


# TODO: How to manage auth?
def bulk_create(handle, data, claims=None, ignore_duplicates=False):
    ver, ep = cache.get_version_and_endpoint(handle)
    # check_write_permission(ep, claims)
    # qry = BulkCreate(ver, ep, data, ignore_duplicates=ignore_duplicates)
    # return qry.execute()


# TODO: How to manage auth?
def bulk_update(handle, data, claims=None):
    ver, ep = cache.get_version_and_endpoint(handle)
    # check_write_permission(ep, claims)
    # qry = BulkUpdate(ver, ep, data)
    # return qry.execute()


def list(handle, include=None, filter=None, order=[], limit=None,
         include_limit=None, offset=None, offset_reverse=False,
         url=None):
    ver, ep = cache.get_version_and_endpoint(handle)
    check_access(ep, 'list')

    # Run the query and iterate the rows. PostgreSQL should manage
    # buffering the results, but I'm not 100% sure that will happen.
    # TODO: Confirm result buffering. If it's not happening will need
    #   to allocate a buffer and return chunks?
    # TODO: Ordering.
    qry = List(
        ver,
        ep,
        include=include,
        filter=Filter(filter),
        order=order,
        limit=limit,
        include_limit=include_limit,
        offset=offset,
        offset_reverse=offset_reverse,
        url=url
    )
    for r in qry.iter_rows():
        yield r


def detail(handle, id, include=[]):
    ver, ep = cache.get_version_and_endpoint(handle)
    check_access(ep, 'detail')
    qry = Detail(
        ver,
        ep,
        id,
        include=include
    )
    for r in qry.iter_rows():
        yield r


def delete(handle, id):
    ver, ep = cache.get_version_and_endpoint(handle)
    check_access(ep, 'delete')
    qry = Delete(ver, ep, id)
    qry.execute()


def get(handle, include=[], filter={}, order=[], id=None):
    if id:
        qry = detail(handle, id, include=include)
    else:
        qry = list(handle, include=include, filter=filter, order=order, limit=1)
    for r in qry:
        return r
    raise DoesNotExist
