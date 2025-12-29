from __future__ import annotations

from collections.abc import Sequence
from typing import (
    Any,
    ClassVar,
    TypeAlias,
    TypeGuard,
    TypeVar,
    final,
    overload,
)

from typing_extensions import Self


@final
class LookaheadMatch:
    characters: ClassVar[str] = ''
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

    def __new__(cls, rule_name: str | None = None, /) -> Self:
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

    def __new__(
        cls, rule_name: str | None = None, /, *, characters: str
    ) -> Self:
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
    def children(self, /) -> Sequence[MatchTreeChild]:
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
        rule_name: str | None = None,
        /,
        *,
        children: Sequence[MatchTreeChild],
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
                    if not is_match_tree_child(child)
                ]
            )
            > 0
        ):
            raise TypeError(
                f'All children must have type {MatchTreeChild}, '
                f'but got {invalid_children!r}.'
            )
        self = super().__new__(cls)
        self._children, self._rule_name = children, rule_name
        return self

    _children: Sequence[MatchTreeChild]
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


@final
class RuleMatch:
    @property
    def characters(self, /) -> str:
        return self._match.characters

    @property
    def characters_count(self, /) -> int:
        return self._match.characters_count

    @property
    def match(self, /) -> AnyMatch:
        return self._match

    @property
    def rule_name(self, /) -> str:
        return self._rule_name

    __slots__ = '_match', '_rule_name'

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {RuleMatch.__qualname__!r} is not an acceptable base type'
        )

    def __new__(cls, rule_name: str, /, *, match: AnyMatch) -> Self:
        _validate_rule_name(rule_name)
        if not isinstance(
            match, LookaheadMatch | MatchLeaf | MatchTree | RuleMatch
        ):
            raise TypeError(type(match))
        self = super().__new__(cls)
        self._match, self._rule_name = match, rule_name
        return self

    _match: AnyMatch
    _rule_name: str

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
                and self._match == other._match
            )
            if isinstance(other, RuleMatch)
            else NotImplemented
        )

    def __repr__(self, /) -> str:
        return (
            f'{type(self).__qualname__}('
            f'rule_name={self._rule_name!r}, '
            f'match={self._match!r}'
            ')'
        )


AnyMatch: TypeAlias = LookaheadMatch | MatchLeaf | MatchTree | RuleMatch
MatchTreeChild: TypeAlias = MatchLeaf | MatchTree | RuleMatch
MatchT_co = TypeVar(
    'MatchT_co',
    LookaheadMatch,
    MatchLeaf,
    MatchTree,
    LookaheadMatch | MatchTree,
    MatchTreeChild,
    AnyMatch,
    RuleMatch,
    covariant=True,
)


def is_match_tree_child(value: AnyMatch, /) -> TypeGuard[MatchTreeChild]:
    return isinstance(value, MatchLeaf | MatchTree) or (
        isinstance(value, RuleMatch) and is_match_tree_child(value.match)
    )


def _validate_rule_name(rule_name: str | None, /) -> None:
    if not isinstance(rule_name, str | None):
        raise TypeError(type(rule_name))
