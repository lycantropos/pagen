from __future__ import annotations

from collections.abc import Sequence
from typing import Any, ClassVar, TypeAlias, TypeVar, final

from typing_extensions import Never, Self, TypeIs, override

from .match import AnyMatch


@final
class MismatchLeaf:
    @property
    def characters(self, /) -> str:
        return self._characters

    @property
    def rule_name(self, /) -> str | None:
        return self._rule_name

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {MismatchLeaf.__qualname__!r} '
            f'is not an acceptable base type'
        )

    @override
    def __new__(cls, rule_name: str | None, /, *, characters: str) -> Self:
        _validate_rule_name(rule_name)
        if not isinstance(characters, str):
            raise TypeError(type(characters))
        self = super().__new__(cls)
        self._characters, self._rule_name = characters, rule_name
        return self

    _characters: str
    _rule_name: str | None

    @override
    def __repr__(self, /) -> str:
        return (
            f'{type(self).__qualname__}'
            '('
            f'{self._rule_name!r}, characters={self._characters!r}'
            ')'
        )


@final
class MismatchTree:
    MIN_CHILDREN_COUNT: ClassVar[int] = 1

    @property
    def children(self, /) -> Sequence[_MismatchTreeChild]:
        return self._children

    @property
    def rule_name(self, /) -> str | None:
        return self._rule_name

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {MismatchLeaf.__qualname__!r} '
            f'is not an acceptable base type'
        )

    @override
    def __new__(
        cls,
        rule_name: str | None,
        /,
        *,
        children: Sequence[AnyMatch | AnyMismatch],
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
                    if not isinstance(child, _MismatchTreeChild)
                ]
            )
            > 0
        ):
            raise TypeError(
                f'All children must have type {_MismatchTreeChild}, '
                f'but got {invalid_children!r}.'
            )
        self = super().__new__(cls)
        self._children, self._rule_name = children, rule_name
        return self

    _children: Sequence[_MismatchTreeChild]
    _rule_name: str | None

    @override
    def __repr__(self, /) -> str:
        return (
            f'{type(self).__qualname__}'
            '('
            f'{self._rule_name!r}, children={self._children!r}'
            ')'
        )


AnyMismatch: TypeAlias = MismatchLeaf | MismatchTree
NoMismatch: TypeAlias = Never
MismatchT_co = TypeVar(
    'MismatchT_co',
    AnyMismatch,
    MismatchLeaf,
    MismatchTree,
    NoMismatch,
    covariant=True,
)


def is_mismatch(value: Any, /) -> TypeIs[AnyMismatch]:
    return isinstance(value, AnyMismatch)


_MismatchTreeChild: TypeAlias = AnyMatch | AnyMismatch


def _validate_rule_name(rule_name: str | None, /) -> None:
    if not isinstance(rule_name, str | None):
        raise TypeError(type(rule_name))
