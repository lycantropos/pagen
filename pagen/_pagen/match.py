from __future__ import annotations

from collections.abc import Sequence
from typing import Any, ClassVar, TypeAlias, TypeVar, final, overload

from typing_extensions import Self


@final
class LookaheadMatch:
    characters_count: ClassVar[int] = 0

    @property
    def rule_name(self, /) -> str | None:
        return self._rule_name

    __slots__ = ('_rule_name',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {LookaheadMatch.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(cls, rule_name: str | None, /) -> Self:
        _validate_rule_name(rule_name)
        self = super().__new__(cls)
        self._rule_name = rule_name
        return self

    _rule_name: str | None

    @overload
    def __eq__(self, other: Self, /) -> bool:
        pass

    @overload
    def __eq__(self, other: Any, /) -> Any:
        pass

    def __eq__(self, other: Any, /) -> Any:
        return (
            self._rule_name == other._rule_name
            if isinstance(other, LookaheadMatch)
            else NotImplemented
        )

    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._rule_name!r})'


@final
class MatchLeaf:
    @property
    def characters(self, /) -> str:
        return self._characters

    @property
    def characters_count(self, /) -> int:
        return len(self._characters)

    @property
    def rule_name(self, /) -> str | None:
        return self._rule_name

    __slots__ = '_characters', '_rule_name'

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {MatchLeaf.__qualname__!r} is not an acceptable base type'
        )

    def __new__(cls, rule_name: str | None, /, *, characters: str) -> Self:
        _validate_rule_name(rule_name)
        if not isinstance(characters, str):
            raise TypeError(type(characters))
        self = super().__new__(cls)
        self._characters, self._rule_name = characters, rule_name
        return self

    _characters: str
    _rule_name: str | None

    @overload
    def __eq__(self, other: Self, /) -> bool:
        pass

    @overload
    def __eq__(self, other: Any, /) -> Any:
        pass

    def __eq__(self, other: Any, /) -> Any:
        return (
            (
                self._rule_name == other._rule_name
                and self._characters == other._characters
            )
            if isinstance(other, MatchLeaf)
            else NotImplemented
        )

    def __repr__(self, /) -> str:
        return (
            f'{type(self).__qualname__}'
            '('
            f'{self._rule_name!r}, '
            f'characters={self._characters!r}'
            ')'
        )


@final
class MatchTree:
    MIN_CHILDREN_COUNT: ClassVar[int] = 1

    @property
    def characters(self, /) -> str:
        return ''.join(child.characters for child in self._children)

    @property
    def characters_count(self, /) -> int:
        return sum(child.characters_count for child in self._children)

    @property
    def children(self, /) -> Sequence[_MatchTreeChild]:
        return self._children

    @property
    def rule_name(self, /) -> str | None:
        return self._rule_name

    __slots__ = '_children', '_rule_name'

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {MatchTree.__qualname__!r} is not an acceptable base type'
        )

    def __new__(
        cls,
        rule_name: str | None,
        /,
        *,
        children: Sequence[MatchLeaf | MatchTree],
    ) -> Self:
        _validate_rule_name(rule_name)
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
                    if not isinstance(child, _MatchTreeChild)
                ]
            )
            > 0
        ):
            raise TypeError(
                f'All children must have type {_MatchTreeChild}, '
                f'but got {invalid_children!r}.'
            )
        self = super().__new__(cls)
        self._children, self._rule_name = children, rule_name
        return self

    _children: Sequence[_MatchTreeChild]
    _rule_name: str | None

    @overload
    def __eq__(self, other: Self, /) -> bool:
        pass

    @overload
    def __eq__(self, other: Any, /) -> Any:
        pass

    def __eq__(self, other: Any, /) -> Any:
        return (
            (
                self._rule_name == other._rule_name
                and self._children == other._children
            )
            if isinstance(other, MatchTree)
            else NotImplemented
        )

    def __repr__(self, /) -> str:
        return (
            f'{type(self).__qualname__}('
            f'{self._rule_name!r}, '
            f'children={self.children!r}'
            ')'
        )


AnyMatch: TypeAlias = LookaheadMatch | MatchLeaf | MatchTree
MatchT_co = TypeVar(
    'MatchT_co',
    LookaheadMatch,
    MatchLeaf,
    MatchTree,
    LookaheadMatch | MatchTree,
    MatchLeaf | MatchTree,
    AnyMatch,
    covariant=True,
)

_MatchTreeChild: TypeAlias = MatchLeaf | MatchTree


def _validate_rule_name(rule_name: str | None, /) -> None:
    if not isinstance(rule_name, str | None):
        raise TypeError(type(rule_name))
