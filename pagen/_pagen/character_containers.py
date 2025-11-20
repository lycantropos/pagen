from __future__ import annotations

from collections.abc import Mapping, Sequence
from itertools import groupby
from operator import eq
from types import MappingProxyType
from typing import Any, TypeGuard, TypeVar, final, overload

from typing_extensions import Self, override

from .constants import (
    CHARACTER_CLASS_SPECIAL_CHARACTERS,
    COMMON_SPECIAL_CHARACTERS_TRANSLATION_TABLE,
)


@final
class CharacterRange:
    __slots__ = '_end', '_start'

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {CharacterRange.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(cls, start: str, end: str, /) -> Self:
        if not isinstance(start, str):
            raise TypeError(type(start))
        if not isinstance(end, str):
            raise TypeError(type(end))
        if ord(start) > ord(end):
            raise ValueError(
                'Range start should not be greater than end, '
                f'but got {start!r} > {end!r}.'
            )
        self = super().__new__(cls)
        self._end, self._start = end, start
        return self

    _end: str
    _start: str

    def __contains__(self, character: str, /) -> bool:
        assert isinstance(character, str), character
        assert len(character) == 1, character
        return self._start <= character <= self._end

    @overload
    def __eq__(self, other: Self, /) -> bool: ...

    @overload
    def __eq__(self, other: Any, /) -> Any: ...

    @override
    def __eq__(self, other: Any, /) -> Any:
        return (
            (self._end == other._end and self._start == other._start)
            if isinstance(other, CharacterRange)
            else NotImplemented
        )

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._start!r}, {self._end!r})'

    @override
    def __str__(self, /) -> str:
        return (
            f'{_escape_character_container_characters(self._start)}'
            '-'
            f'{_escape_character_container_characters(self._end)}'
        )


@final
class CharacterSet:
    __slots__ = ('_elements',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {CharacterSet.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(cls, elements: str, /) -> Self:
        if not isinstance(elements, str):
            raise TypeError(type(elements))
        if len(elements) == 0:
            raise ValueError(
                f'Elements should not be empty, but got: {elements!r}.'
            )
        self = super().__new__(cls)
        self._elements = elements
        return self

    @property
    def elements(self, /) -> str:
        return self._elements

    _elements: str

    def __contains__(self, character: str, /) -> bool:
        assert isinstance(character, str), character
        assert len(character) == 1, character
        return character in self._elements

    @overload
    def __eq__(self, other: Self, /) -> bool: ...

    @overload
    def __eq__(self, other: Any, /) -> Any: ...

    @override
    def __eq__(self, other: Any, /) -> Any:
        return (
            self._elements == other._elements
            if isinstance(other, CharacterSet)
            else NotImplemented
        )

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._elements!r})'

    @override
    def __str__(self, /) -> str:
        return _escape_character_container_characters(self._elements)


def merge_consecutive_character_sets(
    containers: Sequence[CharacterRange | CharacterSet], /
) -> Sequence[CharacterRange | CharacterSet]:
    result: list[CharacterRange | CharacterSet] = []
    for container_cls, container_group in groupby(containers, key=type):
        if not issubclass(container_cls, CharacterSet):
            result.extend(container_group)
            continue
        character_sets = list(container_group)
        if len(character_sets) == 1:
            result.append(character_sets[0])
            continue
        assert _is_character_set_list(character_sets), character_sets
        result.append(
            CharacterSet(
                ''.join(
                    character_set.elements for character_set in character_sets
                )
            )
        )
    return result


def _is_character_set_list(
    value: list[Any], /
) -> TypeGuard[list[CharacterSet]]:
    return all(isinstance(element, CharacterSet) for element in value)


_T = TypeVar('_T')


def _are_sequences_equivalent(
    first: Sequence[_T], second: Sequence[_T], /
) -> bool:
    return len(first) == len(second) and all(map(eq, first, second))


def _escape_character_container_characters(
    value: str,
    /,
    *,
    translation_table: Mapping[int, str] = MappingProxyType(
        {
            **{
                ord(character): '\\' + character  # type: ignore[name-defined]
                for character in CHARACTER_CLASS_SPECIAL_CHARACTERS
            },
            **COMMON_SPECIAL_CHARACTERS_TRANSLATION_TABLE,
        }
    ),
) -> str:
    assert isinstance(value, str), value
    assert len(value) > 0, value
    return value.translate(translation_table)
