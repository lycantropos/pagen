from __future__ import annotations

import sys
from collections.abc import Sequence
from typing import ClassVar, TypeAlias, TypeVar, final

from typing_extensions import Self, override


@final
class MismatchLeaf:
    @property
    def expected_message(self, /) -> str:
        return self._expected_message

    @property
    def origin_name(self, /) -> str:
        return self._origin_name

    @property
    def start_index(self, /) -> int:
        return self._start_index

    @property
    def stop_index(self, /) -> int:
        return self._stop_index

    __slots__ = (
        '_expected_message',
        '_origin_name',
        '_start_index',
        '_stop_index',
    )

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {MismatchLeaf.__qualname__!r} '
            f'is not an acceptable base type'
        )

    @override
    def __new__(
        cls,
        origin_name: str,
        /,
        *,
        expected_message: str,
        start_index: int,
        stop_index: int,
    ) -> Self:
        _validate_origin_name(origin_name)
        _validate_index(start_index)
        _validate_index(stop_index)
        if start_index >= stop_index:
            raise ValueError((start_index, stop_index))
        self = super().__new__(cls)
        (
            self._expected_message,
            self._origin_name,
            self._start_index,
            self._stop_index,
        ) = (expected_message, origin_name, start_index, stop_index)
        return self

    _expected_message: str
    _origin_name: str
    _start_index: int
    _stop_index: int

    @override
    def __repr__(self, /) -> str:
        return (
            f'{type(self).__qualname__}'
            '('
            f'{self._origin_name!r}, '
            f'expected_message={self._expected_message!r}, '
            f'start_index={self._start_index!r}, '
            f'stop_index={self._stop_index!r}'
            ')'
        )


@final
class MismatchTree:
    MIN_CHILDREN_COUNT: ClassVar[int] = 1

    @property
    def children(self, /) -> Sequence[AnyMismatch]:
        return self._children

    @property
    def origin_name(self, /) -> str:
        return self._origin_name

    @property
    def start_index(self, /) -> int:
        return self._children[-1].start_index

    @property
    def stop_index(self, /) -> int:
        return self._children[-1].stop_index

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {MismatchLeaf.__qualname__!r} '
            f'is not an acceptable base type'
        )

    @override
    def __new__(
        cls, origin_name: str, /, *, children: Sequence[AnyMismatch]
    ) -> Self:
        _validate_origin_name(origin_name)
        if len(children) < cls.MIN_CHILDREN_COUNT:
            raise ValueError(
                f'Expected at least {cls.MIN_CHILDREN_COUNT!r} children, '
                f'but got {children!r}.'
            )
        if (
            len(
                invalid_children := [
                    child
                    for child in children
                    if not isinstance(child, AnyMismatch)
                ]
            )
            > 0
        ):
            raise TypeError(
                f'All children must have type {AnyMismatch}, '
                f'but got {invalid_children!r}.'
            )
        self = super().__new__(cls)
        self._children, self._origin_name = children, origin_name
        return self

    _children: Sequence[AnyMismatch]
    _origin_name: str

    @override
    def __repr__(self, /) -> str:
        return (
            f'{type(self).__qualname__}'
            '('
            f'{self._origin_name!r}, children={self._children!r}'
            ')'
        )


AnyMismatch: TypeAlias = MismatchLeaf | MismatchTree
MismatchT_co = TypeVar(
    'MismatchT_co', MismatchLeaf, MismatchTree, AnyMismatch, covariant=True
)


def _validate_index(index: int) -> None:
    if not isinstance(index, int):
        raise TypeError(type(index))
    if index not in range(sys.maxsize + 1):
        raise ValueError(index)


def _validate_origin_name(value: str, /) -> None:
    if not isinstance(value, str):
        raise TypeError(type(value))
    if len(value.strip()) < 1:
        raise ValueError(value)
