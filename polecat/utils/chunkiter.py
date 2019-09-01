from itertools import zip_longest

from .optiondict import Undefined


def chunkiter(iterable, size=10):
    args = [iter(iterable)]*size
    for ii in zip_longest(*args, fillvalue=Undefined):
        if tuple(ii)[-1] == Undefined:
            yield tuple(v for v in ii if v != Undefined)
        else:
            yield ii
