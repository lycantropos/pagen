import inspect
from collections.abc import Iterable
from typing import TypeVar

import pagen

_T = TypeVar('_T')


def to_package_non_abstract_subclasses(cls: type[_T], /) -> Iterable[type[_T]]:
    for subclass in cls.__subclasses__():
        yield from to_package_non_abstract_subclasses(subclass)
        if inspect.isabstract(subclass):
            continue
        if subclass.__module__ == pagen.__name__:
            continue
        yield subclass
