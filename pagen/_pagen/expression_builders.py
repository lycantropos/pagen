from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping, Sequence
from types import UnionType
from typing import Any, ClassVar, Generic, TypeGuard, final

from typing_extensions import Self, override

from .character_containers import (
    CharacterRange,
    CharacterSet,
    merge_consecutive_character_sets,
)
from .expressions import (
    AnyCharacterExpression,
    CharacterClassExpression,
    ComplementedCharacterClassExpression,
    DoubleQuotedLiteralExpression,
    ExactRepetitionExpression,
    Expression,
    NegativeLookaheadExpression,
    OneOrMoreExpression,
    OptionalExpression,
    PositiveLookaheadExpression,
    PositiveOrMoreExpression,
    PositiveRepetitionRangeExpression,
    PrioritizedChoiceExpression,
    RuleReference,
    SequenceExpression,
    SingleQuotedLiteralExpression,
    ZeroOrMoreExpression,
    ZeroRepetitionRangeExpression,
)
from .match import AnyMatch, LookaheadMatch, MatchLeaf, MatchT_co, MatchTree
from .mismatch import AnyMismatch, MismatchLeaf, MismatchT_co, MismatchTree


class ExpressionBuilder(ABC, Generic[MatchT_co, MismatchT_co]):
    @abstractmethod
    def always_matches(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def build(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
    ) -> Expression[MatchT_co, MismatchT_co]:
        raise NotImplementedError

    @abstractmethod
    def is_left_recursive(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def is_nullable(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def is_terminating(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        is_leftmost: bool,
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        raise NotImplementedError

    def to_match_classes(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[MatchT_co]]:
        yield from self._to_match_classes_impl(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )

    def to_mismatch_classes(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[MismatchT_co]]:
        yield from self._to_mismatch_classes_impl(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )

    __slots__ = ()

    @abstractmethod
    def _to_match_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[MatchT_co]]:
        raise NotImplementedError

    @abstractmethod
    def _to_mismatch_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[MismatchT_co]]:
        raise NotImplementedError

    @abstractmethod
    def __repr__(self, /) -> str:
        raise NotImplementedError


@final
class AnyCharacterExpressionBuilder(
    ExpressionBuilder[MatchLeaf, MismatchLeaf]
):
    @override
    def always_matches(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return False

    @override
    def build(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
    ) -> AnyCharacterExpression:
        return AnyCharacterExpression()

    @override
    def is_left_recursive(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return False

    @override
    def is_nullable(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return False

    @override
    def is_terminating(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        is_leftmost: bool,
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return True

    __slots__ = ()

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {AnyCharacterExpressionBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

    @override
    def _to_match_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[MatchLeaf]]:
        yield MatchLeaf

    @override
    def _to_mismatch_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[MismatchLeaf]]:
        yield MismatchLeaf

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}()'


@final
class CharacterClassExpressionBuilder(
    ExpressionBuilder[MatchLeaf, MismatchLeaf]
):
    @override
    def always_matches(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return False

    @override
    def build(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
    ) -> CharacterClassExpression:
        return CharacterClassExpression(self._elements)

    @override
    def is_left_recursive(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return False

    @override
    def is_nullable(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return False

    @override
    def is_terminating(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        is_leftmost: bool,
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return True

    __slots__ = ('_elements',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {CharacterClassExpressionBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

    @override
    def __new__(
        cls, elements: Sequence[CharacterRange | CharacterSet], /
    ) -> Self:
        assert len(elements) > 0, elements
        self = super().__new__(cls)
        self._elements = merge_consecutive_character_sets(elements)
        return self

    _elements: Sequence[CharacterRange | CharacterSet]

    @override
    def _to_match_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[MatchLeaf]]:
        yield MatchLeaf

    @override
    def _to_mismatch_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[MismatchLeaf]]:
        yield MismatchLeaf

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._elements!r})'


@final
class ComplementedCharacterClassExpressionBuilder(
    ExpressionBuilder[MatchLeaf, MismatchLeaf]
):
    @override
    def always_matches(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return False

    @override
    def build(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
    ) -> ComplementedCharacterClassExpression:
        return ComplementedCharacterClassExpression(self._elements)

    @override
    def is_left_recursive(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return False

    @override
    def is_nullable(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return False

    @override
    def is_terminating(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        is_leftmost: bool,
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return True

    __slots__ = ('_elements',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            'type '
            f'{ComplementedCharacterClassExpressionBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

    @override
    def __new__(
        cls, elements: Sequence[CharacterRange | CharacterSet], /
    ) -> Self:
        assert len(elements) > 0, elements
        self = super().__new__(cls)
        self._elements = merge_consecutive_character_sets(elements)
        return self

    _elements: Sequence[CharacterRange | CharacterSet]

    @override
    def _to_match_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[MatchLeaf]]:
        yield MatchLeaf

    @override
    def _to_mismatch_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[MismatchLeaf]]:
        yield MismatchLeaf

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._elements!r})'


@final
class ExactRepetitionExpressionBuilder(
    ExpressionBuilder[MatchTree, MismatchTree]
):
    @property
    def expression_builder_index(self, /) -> int:
        return self._expression_builder_index

    @override
    def always_matches(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).always_matches(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )

    @override
    def build(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
    ) -> ExactRepetitionExpression:
        expression_builder = self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        )
        _check_that_expression_builder_is_progressing(
            expression_builder,
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        )
        return ExactRepetitionExpression(
            expression_builder.build(
                expression_builders=expression_builders,
                rule_expression_builder_indices=rule_expression_builder_indices,
            ),
            self._count,
        )

    @override
    def is_left_recursive(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).is_left_recursive(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )

    @override
    def is_nullable(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return False

    @override
    def is_terminating(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        is_leftmost: bool,
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).is_terminating(
            expression_builders=expression_builders,
            is_leftmost=is_leftmost,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )

    _count: int
    _expression_builder_index: int

    def _get_expression_builder(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
    ) -> ExpressionBuilder[MatchLeaf | MatchTree, AnyMismatch]:
        result = expression_builders[self._expression_builder_index]
        assert _is_expression_builder(
            result,
            expected_match_cls=MatchLeaf | MatchTree,
            expected_mismatch_cls=AnyMismatch,
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ), result
        return result

    @override
    def _to_match_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[MatchTree]]:
        yield MatchTree

    @override
    def _to_mismatch_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[MismatchTree]]:
        yield MismatchTree

    __slots__ = '_count', '_expression_builder_index'

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {ExactRepetitionExpressionBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

    @override
    def __new__(cls, expression_builder_index: int, count: int, /) -> Self:
        _validate_repetition_expression_builder_bound(count)
        _validate_expression_builder_index(expression_builder_index)
        if count < ExactRepetitionExpression.MIN_COUNT:
            raise ValueError(
                'Repetition count should not be '
                f'less than {ExactRepetitionExpression.MIN_COUNT!r}, '
                f'but got {count!r}.'
            )
        self = super().__new__(cls)
        self._count, self._expression_builder_index = (
            count,
            expression_builder_index,
        )
        return self

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression_builder_index!r})'


class LiteralExpressionBuilder(ExpressionBuilder[MatchLeaf, MismatchLeaf]):
    @override
    def always_matches(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return False

    @override
    def is_left_recursive(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return False

    @override
    def is_nullable(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return False

    @override
    def is_terminating(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        is_leftmost: bool,
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return True

    __slots__ = ()

    @override
    def _to_match_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[MatchLeaf]]:
        yield MatchLeaf

    @override
    def _to_mismatch_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[MismatchLeaf]]:
        yield MismatchLeaf


@final
class DoubleQuotedLiteralExpressionBuilder(LiteralExpressionBuilder):
    @override
    def build(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
    ) -> DoubleQuotedLiteralExpression:
        return DoubleQuotedLiteralExpression(self._value)

    __slots__ = ('_value',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {DoubleQuotedLiteralExpressionBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

    @override
    def __new__(cls, value: str, /) -> Self:
        assert len(value) > 0, value
        self = super().__new__(cls)
        self._value = value
        return self

    _value: str

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._value!r})'


@final
class SingleQuotedLiteralExpressionBuilder(LiteralExpressionBuilder):
    @override
    def build(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
    ) -> SingleQuotedLiteralExpression:
        return SingleQuotedLiteralExpression(self._value)

    __slots__ = ('_value',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {SingleQuotedLiteralExpressionBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

    @override
    def __new__(cls, value: str, /) -> Self:
        assert len(value) > 0, value
        self = super().__new__(cls)
        self._value = value
        return self

    _value: str

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._value!r})'


@final
class NegativeLookaheadExpressionBuilder(
    ExpressionBuilder[LookaheadMatch, MismatchLeaf]
):
    @property
    def expression_builder_index(self, /) -> int:
        return self._expression_builder_index

    @override
    def always_matches(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).always_matches(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )

    @override
    def build(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
    ) -> NegativeLookaheadExpression:
        expression_builder = self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        )
        _check_that_expression_builder_is_progressing(
            expression_builder,
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        )
        return NegativeLookaheadExpression(
            expression_builder.build(
                expression_builders=expression_builders,
                rule_expression_builder_indices=rule_expression_builder_indices,
            )
        )

    @override
    def is_left_recursive(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).is_left_recursive(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )

    @override
    def is_nullable(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return True

    @override
    def is_terminating(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        is_leftmost: bool,
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).is_terminating(
            expression_builders=expression_builders,
            is_leftmost=is_leftmost,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )

    _expression_builder_index: int

    def _get_expression_builder(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
    ) -> ExpressionBuilder[MatchLeaf | MatchTree, AnyMismatch]:
        result = expression_builders[self._expression_builder_index]
        assert _is_expression_builder(
            result,
            expected_match_cls=MatchLeaf | MatchTree,
            expected_mismatch_cls=AnyMismatch,
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ), result
        return result

    @override
    def _to_match_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[LookaheadMatch]]:
        yield LookaheadMatch

    @override
    def _to_mismatch_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[MismatchLeaf]]:
        yield MismatchLeaf

    __slots__ = ('_expression_builder_index',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {NegativeLookaheadExpressionBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

    @override
    def __new__(cls, expression_builder_index: int, /) -> Self:
        _validate_expression_builder_index(expression_builder_index)
        self = super().__new__(cls)
        self._expression_builder_index = expression_builder_index
        return self

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression_builder_index!r})'


@final
class OneOrMoreExpressionBuilder(ExpressionBuilder[MatchTree, MismatchTree]):
    @property
    def expression_builder_index(self, /) -> int:
        return self._expression_builder_index

    @override
    def always_matches(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).always_matches(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )

    @override
    def build(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
    ) -> OneOrMoreExpression:
        expression_builder = self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        )
        _check_that_expression_builder_is_progressing(
            expression_builder,
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        )
        return OneOrMoreExpression(
            expression_builder.build(
                expression_builders=expression_builders,
                rule_expression_builder_indices=rule_expression_builder_indices,
            )
        )

    @override
    def is_left_recursive(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).is_left_recursive(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )

    @override
    def is_nullable(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return expression_builders[self._expression_builder_index].is_nullable(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )

    @override
    def is_terminating(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        is_leftmost: bool,
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).is_terminating(
            expression_builders=expression_builders,
            is_leftmost=is_leftmost,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )

    __slots__ = ('_expression_builder_index',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {OneOrMoreExpressionBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

    @override
    def __new__(cls, expression_builder_index: int, /) -> Self:
        _validate_expression_builder_index(expression_builder_index)
        self = super().__new__(cls)
        self._expression_builder_index = expression_builder_index
        return self

    _expression_builder_index: int

    def _get_expression_builder(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
    ) -> ExpressionBuilder[MatchLeaf | MatchTree, AnyMismatch]:
        result = expression_builders[self._expression_builder_index]
        assert _is_expression_builder(
            result,
            expected_match_cls=MatchLeaf | MatchTree,
            expected_mismatch_cls=AnyMismatch,
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ), result
        return result

    @override
    def _to_match_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[MatchTree]]:
        yield MatchTree

    @override
    def _to_mismatch_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[MismatchTree]]:
        yield MismatchTree

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression_builder_index!r})'


@final
class OptionalExpressionBuilder(ExpressionBuilder[AnyMatch, AnyMismatch]):
    @property
    def expression_builder_index(self, /) -> int:
        return self._expression_builder_index

    @override
    def always_matches(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return True

    @override
    def build(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
    ) -> OptionalExpression:
        expression_builder = self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        )
        _check_that_expression_builder_is_progressing(
            expression_builder,
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        )
        return OptionalExpression(
            expression_builder.build(
                expression_builders=expression_builders,
                rule_expression_builder_indices=rule_expression_builder_indices,
            )
        )

    @override
    def is_left_recursive(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).is_left_recursive(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )

    @override
    def is_nullable(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return True

    @override
    def is_terminating(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        is_leftmost: bool,
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return not is_leftmost or self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).is_terminating(
            expression_builders=expression_builders,
            is_leftmost=is_leftmost,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )

    _expression_builder_index: int

    def _get_expression_builder(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
    ) -> ExpressionBuilder[MatchLeaf | MatchTree, AnyMismatch]:
        result = expression_builders[self._expression_builder_index]
        assert _is_expression_builder(
            result,
            expected_match_cls=MatchLeaf | MatchTree,
            expected_mismatch_cls=AnyMismatch,
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ), result
        return result

    @override
    def _to_match_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[AnyMatch]]:
        yield LookaheadMatch
        yield from self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).to_match_classes(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )

    @override
    def _to_mismatch_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[AnyMismatch]]:
        yield from self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).to_mismatch_classes(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )

    __slots__ = ('_expression_builder_index',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {OptionalExpressionBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

    @override
    def __new__(cls, expression_builder_index: int, /) -> Self:
        _validate_expression_builder_index(expression_builder_index)
        self = super().__new__(cls)
        self._expression_builder_index = expression_builder_index
        return self

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression_builder_index!r})'


@final
class PositiveLookaheadExpressionBuilder(
    ExpressionBuilder[LookaheadMatch, MismatchLeaf]
):
    @property
    def expression_builder_index(self, /) -> int:
        return self._expression_builder_index

    @override
    def always_matches(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).always_matches(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )

    @override
    def build(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
    ) -> PositiveLookaheadExpression:
        expression_builder = self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        )
        _check_that_expression_builder_is_progressing(
            expression_builder,
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        )
        return PositiveLookaheadExpression(
            expression_builder.build(
                expression_builders=expression_builders,
                rule_expression_builder_indices=rule_expression_builder_indices,
            )
        )

    @override
    def is_left_recursive(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).is_left_recursive(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )

    @override
    def is_nullable(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return True

    @override
    def is_terminating(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        is_leftmost: bool,
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).is_terminating(
            expression_builders=expression_builders,
            is_leftmost=is_leftmost,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )

    _expression_builder_index: int

    def _get_expression_builder(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
    ) -> ExpressionBuilder[MatchLeaf | MatchTree, AnyMismatch]:
        result = expression_builders[self._expression_builder_index]
        assert _is_expression_builder(
            result,
            expected_match_cls=MatchLeaf | MatchTree,
            expected_mismatch_cls=AnyMismatch,
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ), result
        return result

    @override
    def _to_match_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[LookaheadMatch]]:
        yield LookaheadMatch

    @override
    def _to_mismatch_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[MismatchLeaf]]:
        yield MismatchLeaf

    __slots__ = ('_expression_builder_index',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {PositiveLookaheadExpressionBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

    @override
    def __new__(cls, expression_builder_index: int, /) -> Self:
        self = super().__new__(cls)
        self._expression_builder_index = expression_builder_index
        return self

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression_builder_index!r})'


@final
class PositiveOrMoreExpressionBuilder(
    ExpressionBuilder[MatchTree, MismatchTree]
):
    @property
    def expression_builder_index(self, /) -> int:
        return self._expression_builder_index

    @override
    def always_matches(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).always_matches(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )

    @override
    def build(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
    ) -> PositiveOrMoreExpression:
        expression_builder = self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        )
        _check_that_expression_builder_is_progressing(
            expression_builder,
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        )
        return PositiveOrMoreExpression(
            expression_builder.build(
                expression_builders=expression_builders,
                rule_expression_builder_indices=rule_expression_builder_indices,
            ),
            self._start,
        )

    @override
    def is_left_recursive(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).is_left_recursive(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )

    @override
    def is_nullable(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return expression_builders[self._expression_builder_index].is_nullable(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )

    @override
    def is_terminating(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        is_leftmost: bool,
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).is_terminating(
            expression_builders=expression_builders,
            is_leftmost=is_leftmost,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )

    _expression_builder_index: int
    _start: int

    def _get_expression_builder(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
    ) -> ExpressionBuilder[MatchLeaf | MatchTree, AnyMismatch]:
        result = expression_builders[self._expression_builder_index]
        assert _is_expression_builder(
            result,
            expected_match_cls=MatchLeaf | MatchTree,
            expected_mismatch_cls=AnyMismatch,
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ), result
        return result

    @override
    def _to_match_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[MatchTree]]:
        yield MatchTree

    @override
    def _to_mismatch_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[MismatchTree]]:
        yield MismatchTree

    __slots__ = '_expression_builder_index', '_start'

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {PositiveOrMoreExpressionBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

    @override
    def __new__(cls, expression_builder_index: int, start: int, /) -> Self:
        _validate_repetition_expression_builder_bound(start)
        _validate_expression_builder_index(expression_builder_index)
        if start < PositiveOrMoreExpression.MIN_START:
            raise ValueError(
                'Repetition start should not be '
                f'less than {PositiveOrMoreExpression.MIN_START!r}, '
                f'but got {start!r}.'
            )
        self = super().__new__(cls)
        self._expression_builder_index, self._start = (
            expression_builder_index,
            start,
        )
        return self

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression_builder_index!r})'


@final
class PositiveRepetitionRangeExpressionBuilder(
    ExpressionBuilder[MatchTree, MismatchTree]
):
    @property
    def expression_builder_index(self, /) -> int:
        return self._expression_builder_index

    @override
    def always_matches(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).always_matches(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )

    @override
    def build(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
    ) -> PositiveRepetitionRangeExpression:
        expression_builder = self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        )
        _check_that_expression_builder_is_progressing(
            expression_builder,
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        )
        return PositiveRepetitionRangeExpression(
            expression_builder.build(
                expression_builders=expression_builders,
                rule_expression_builder_indices=rule_expression_builder_indices,
            ),
            self._start,
            self._end,
        )

    @override
    def is_left_recursive(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).is_left_recursive(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )

    @override
    def is_nullable(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return expression_builders[self._expression_builder_index].is_nullable(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )

    @override
    def is_terminating(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        is_leftmost: bool,
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).is_terminating(
            expression_builders=expression_builders,
            is_leftmost=is_leftmost,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )

    _end: int
    _expression_builder_index: int
    _start: int

    def _get_expression_builder(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
    ) -> ExpressionBuilder[MatchLeaf | MatchTree, AnyMismatch]:
        result = expression_builders[self._expression_builder_index]
        assert _is_expression_builder(
            result,
            expected_match_cls=MatchLeaf | MatchTree,
            expected_mismatch_cls=AnyMismatch,
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ), result
        return result

    @override
    def _to_match_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[MatchTree]]:
        yield MatchTree

    @override
    def _to_mismatch_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[MismatchTree]]:
        yield MismatchTree

    __slots__ = '_end', '_expression_builder_index', '_start'

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {PositiveRepetitionRangeExpressionBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

    @override
    def __new__(
        cls, expression_builder_index: int, start: int, end: int, /
    ) -> Self:
        _validate_repetition_expression_builder_bound(start)
        _validate_repetition_expression_builder_bound(end)
        _validate_expression_builder_index(expression_builder_index)
        if start < PositiveRepetitionRangeExpression.MIN_START:
            raise ValueError(
                'Repetition range start should not be '
                f'less than {PositiveRepetitionRangeExpression.MIN_START!r}, '
                f'but got {start!r}.'
            )
        if start >= end:
            raise ValueError(
                'Repetition range start should be less than end, '
                f'but got {start!r} >= {end!r}.'
            )
        self = super().__new__(cls)
        self._expression_builder_index, self._end, self._start = (
            expression_builder_index,
            end,
            start,
        )
        return self

    @override
    def __repr__(self, /) -> str:
        return (
            f'{type(self).__qualname__}'
            '('
            f'{self._expression_builder_index!r}, '
            f'{self._start!r}, '
            f'{self._end!r}'
            ')'
        )


@final
class PrioritizedChoiceExpressionBuilder(
    ExpressionBuilder[AnyMatch, MismatchTree]
):
    MIN_VARIANT_BUILDERS_COUNT: ClassVar[int] = 2

    @property
    def variant_builder_indices(self, /) -> Sequence[int]:
        return self._variant_builder_indices

    @override
    def always_matches(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return any(
            expression_builders[variant_builder_index].always_matches(
                expression_builders=expression_builders,
                rule_expression_builder_indices=rule_expression_builder_indices,
                visited_rule_names=visited_rule_names,
            )
            for variant_builder_index in self._variant_builder_indices
        )

    @override
    def build(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
    ) -> PrioritizedChoiceExpression:
        variant_builders = [
            expression_builders[variant_builder_index]
            for variant_builder_index in self._variant_builder_indices
        ]
        if (
            len(
                always_matching_variants := [
                    variant_builder
                    for variant_builder in variant_builders[:-1]
                    if variant_builder.always_matches(
                        expression_builders=expression_builders,
                        rule_expression_builder_indices=(
                            rule_expression_builder_indices
                        ),
                        visited_rule_names=set(),
                    )
                ]
            )
            > 0
        ):
            raise ValueError(
                'All variants (except maybe last) '
                'should not be always matching, '
                f'but got: {", ".join(map(repr, always_matching_variants))}.'
            )
        return PrioritizedChoiceExpression(
            [
                variant_builder.build(
                    expression_builders=expression_builders,
                    rule_expression_builder_indices=(
                        rule_expression_builder_indices
                    ),
                )
                for variant_builder in variant_builders
            ]
        )

    @override
    def is_left_recursive(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return any(
            expression_builders[variant_builder_index].is_left_recursive(
                expression_builders=expression_builders,
                rule_expression_builder_indices=rule_expression_builder_indices,
                visited_rule_names=visited_rule_names,
            )
            for variant_builder_index in self._variant_builder_indices
        )

    @override
    def is_nullable(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return any(
            expression_builders[variant_builder_index].is_nullable(
                expression_builders=expression_builders,
                rule_expression_builder_indices=rule_expression_builder_indices,
                visited_rule_names=visited_rule_names,
            )
            for variant_builder_index in self._variant_builder_indices
        )

    @override
    def is_terminating(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        is_leftmost: bool,
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return any(
            expression_builders[variant_builder_index].is_terminating(
                expression_builders=expression_builders,
                is_leftmost=is_leftmost,
                rule_expression_builder_indices=rule_expression_builder_indices,
                visited_rule_names=visited_rule_names,
            )
            for variant_builder_index in self._variant_builder_indices
        )

    _variant_builder_indices: Sequence[int]

    @override
    def _to_match_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[AnyMatch]]:
        for variant_builder_index in self._variant_builder_indices:
            yield from expression_builders[
                variant_builder_index
            ].to_match_classes(
                expression_builders=expression_builders,
                rule_expression_builder_indices=rule_expression_builder_indices,
                visited_rule_names=visited_rule_names,
            )

    @override
    def _to_mismatch_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[MismatchTree]]:
        yield MismatchTree

    __slots__ = ('_variant_builder_indices',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {PrioritizedChoiceExpressionBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

    @override
    def __new__(cls, variant_builder_indices: Sequence[int], /) -> Self:
        if len(variant_builder_indices) < cls.MIN_VARIANT_BUILDERS_COUNT:
            raise ValueError(
                f'{cls.__qualname__!r} should have '
                f'at least {cls.MIN_VARIANT_BUILDERS_COUNT!r} '
                'variant builders, '
                f'but got {len(variant_builder_indices)!r}.'
            )
        if (
            len(
                invalid_type_variant_builder_indices := [
                    variant_builder_index
                    for variant_builder_index in variant_builder_indices
                    if not isinstance(variant_builder_index, int)
                ]
            )
            > 0
        ):
            raise TypeError(invalid_type_variant_builder_indices)
        if (
            len(
                invalid_value_variant_builder_indices := [
                    variant_builder_index
                    for variant_builder_index in variant_builder_indices
                    if variant_builder_index not in range(sys.maxsize + 1)
                ]
            )
            > 0
        ):
            raise ValueError(invalid_value_variant_builder_indices)
        self = super().__new__(cls)
        self._variant_builder_indices = variant_builder_indices
        return self

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._variant_builder_indices!r})'


@final
class RuleReferenceBuilder(ExpressionBuilder[AnyMatch, AnyMismatch]):
    @override
    def always_matches(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        if self._name in visited_rule_names:
            return True
        visited_rule_names.add(self._name)
        result = self._resolve(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).always_matches(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )
        visited_rule_names.remove(self._name)
        return result

    @override
    def build(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
    ) -> RuleReference:
        cursor = self
        visited_rule_names: list[str] = []
        while True:
            cursor_name: str = cursor._name
            if cursor_name in visited_rule_names:
                cycle_names = [
                    *visited_rule_names[
                        visited_rule_names.index(cursor_name) :
                    ],
                    cursor_name,
                ]
                raise ValueError(f'Cycle detected: {cycle_names!r}.')
            visited_rule_names.append(cursor_name)
            try:
                candidate = expression_builders[
                    rule_expression_builder_indices[cursor._name]
                ]
            except KeyError:
                raise ValueError(
                    f'Name {cursor_name!r} is not found in rules.'
                ) from None
            if not isinstance(candidate, RuleReferenceBuilder):
                return RuleReference(
                    self._name,
                    match_classes=list(
                        candidate.to_match_classes(
                            expression_builders=expression_builders,
                            rule_expression_builder_indices=(
                                rule_expression_builder_indices
                            ),
                            visited_rule_names=set(),
                        )
                    ),
                    mismatch_classes=list(
                        candidate.to_mismatch_classes(
                            expression_builders=expression_builders,
                            rule_expression_builder_indices=(
                                rule_expression_builder_indices
                            ),
                            visited_rule_names=set(),
                        )
                    ),
                )
            cursor = candidate

    @override
    def is_left_recursive(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        if self._name in visited_rule_names:
            return True
        visited_rule_names.add(self._name)
        result = self._resolve(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).is_left_recursive(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )
        visited_rule_names.remove(self._name)
        return result

    @override
    def is_nullable(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        if self._name in visited_rule_names:
            return False
        visited_rule_names.add(self._name)
        result = self._resolve(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).is_nullable(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )
        visited_rule_names.remove(self._name)
        return result

    @override
    def is_terminating(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        is_leftmost: bool,
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        if self._name in visited_rule_names:
            return False
        visited_rule_names.add(self._name)
        result = self._resolve(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).is_terminating(
            expression_builders=expression_builders,
            is_leftmost=is_leftmost,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )
        visited_rule_names.remove(self._name)
        return result

    _name: str

    def _resolve(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
    ) -> ExpressionBuilder[AnyMatch, AnyMismatch]:
        return expression_builders[rule_expression_builder_indices[self._name]]

    @override
    def _to_match_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[AnyMatch]]:
        if self._name in visited_rule_names:
            return
        visited_rule_names.add(self._name)
        yield from self._resolve(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).to_match_classes(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )
        visited_rule_names.remove(self._name)

    @override
    def _to_mismatch_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[AnyMismatch]]:
        if self._name in visited_rule_names:
            return
        visited_rule_names.add(self._name)
        yield from self._resolve(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).to_mismatch_classes(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )
        visited_rule_names.remove(self._name)

    __slots__ = ('_name',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {RuleReferenceBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

    @override
    def __new__(cls, name: str, /) -> Self:
        assert len(name) > 0, name
        self = super().__new__(cls)
        self._name = name
        return self

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._name!r})'


@final
class SequenceExpressionBuilder(ExpressionBuilder[MatchTree, MismatchTree]):
    MIN_ELEMENT_BUILDERS_COUNT: ClassVar[int] = 2

    @property
    def element_builder_indices(self, /) -> Sequence[int]:
        return self._element_builder_indices

    @override
    def always_matches(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return False

    @override
    def build(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
    ) -> SequenceExpression:
        element_builders = [
            expression_builders[element_builder_index]
            for element_builder_index in self._element_builder_indices
        ]
        if all(
            element_builder.is_nullable(
                expression_builders=expression_builders,
                rule_expression_builder_indices=(
                    rule_expression_builder_indices
                ),
                visited_rule_names=set(),
            )
            for element_builder in element_builders
        ):
            raise ValueError(
                f'{type(self).__qualname__!r} should have '
                'at least one non-nullable element builder, '
                f'but got: {", ".join(map(repr, element_builders))}.'
            )
        return SequenceExpression(
            [
                element_builder.build(
                    expression_builders=expression_builders,
                    rule_expression_builder_indices=(
                        rule_expression_builder_indices
                    ),
                )
                for element_builder in element_builders
            ]
        )

    @override
    def is_left_recursive(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        for element_builder_index in self._element_builder_indices:
            element_builder = expression_builders[element_builder_index]
            if isinstance(
                element_builder,
                (
                    NegativeLookaheadExpressionBuilder
                    | PositiveLookaheadExpressionBuilder
                ),
            ):
                if element_builder.is_left_recursive(
                    expression_builders=expression_builders,
                    rule_expression_builder_indices=rule_expression_builder_indices,
                    visited_rule_names=visited_rule_names,
                ):
                    return True
                continue
            return element_builder.is_left_recursive(
                expression_builders=expression_builders,
                rule_expression_builder_indices=rule_expression_builder_indices,
                visited_rule_names=visited_rule_names,
            )
        raise ValueError('Sequence consists of non-left recursive lookaheads.')

    @override
    def is_nullable(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return False

    @override
    def is_terminating(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        is_leftmost: bool,
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return expression_builders[
            self._element_builder_indices[0]
        ].is_terminating(
            expression_builders=expression_builders,
            is_leftmost=is_leftmost,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        ) and all(
            expression_builders[element_builder_index].is_terminating(
                expression_builders=expression_builders,
                is_leftmost=False,
                rule_expression_builder_indices=rule_expression_builder_indices,
                visited_rule_names=visited_rule_names,
            )
            for element_builder_index in self._element_builder_indices[1:]
        )

    _element_builder_indices: Sequence[int]

    @override
    def _to_match_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[MatchTree]]:
        yield MatchTree

    @override
    def _to_mismatch_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[MismatchTree]]:
        yield MismatchTree

    __slots__ = ('_element_builder_indices',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {SequenceExpressionBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

    @override
    def __new__(cls, element_builder_indices: Sequence[int], /) -> Self:
        if len(element_builder_indices) < cls.MIN_ELEMENT_BUILDERS_COUNT:
            raise ValueError(
                f'{cls.__qualname__!r} should have '
                f'at least {cls.MIN_ELEMENT_BUILDERS_COUNT!r} '
                'element builders, '
                f'but got {len(element_builder_indices)!r}.'
            )
        if (
            len(
                invalid_type_element_builder_indices := [
                    element_builder_index
                    for element_builder_index in element_builder_indices
                    if not isinstance(element_builder_index, int)
                ]
            )
            > 0
        ):
            raise TypeError(invalid_type_element_builder_indices)
        if (
            len(
                invalid_value_element_builder_indices := [
                    element_builder_index
                    for element_builder_index in element_builder_indices
                    if element_builder_index not in range(sys.maxsize + 1)
                ]
            )
            > 0
        ):
            raise ValueError(invalid_value_element_builder_indices)
        self = super().__new__(cls)
        self._element_builder_indices = element_builder_indices
        return self

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._element_builder_indices!r})'


@final
class ZeroOrMoreExpressionBuilder(
    ExpressionBuilder[LookaheadMatch | MatchTree, AnyMismatch]
):
    @property
    def expression_builder_index(self, /) -> int:
        return self._expression_builder_index

    @override
    def always_matches(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return True

    @override
    def build(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
    ) -> ZeroOrMoreExpression:
        expression_builder = self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        )
        _check_that_expression_builder_is_progressing(
            expression_builder,
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        )
        return ZeroOrMoreExpression(
            expression_builder.build(
                expression_builders=expression_builders,
                rule_expression_builder_indices=rule_expression_builder_indices,
            )
        )

    @override
    def is_left_recursive(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).is_left_recursive(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )

    @override
    def is_nullable(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return True

    @override
    def is_terminating(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        is_leftmost: bool,
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return not is_leftmost or self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).is_terminating(
            expression_builders=expression_builders,
            is_leftmost=is_leftmost,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )

    _expression_builder_index: int

    def _get_expression_builder(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
    ) -> ExpressionBuilder[MatchLeaf | MatchTree, AnyMismatch]:
        result = expression_builders[self._expression_builder_index]
        assert _is_expression_builder(
            result,
            expected_match_cls=MatchLeaf | MatchTree,
            expected_mismatch_cls=AnyMismatch,
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ), result
        return result

    @override
    def _to_match_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[LookaheadMatch | MatchTree]]:
        yield LookaheadMatch
        yield MatchTree

    @override
    def _to_mismatch_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[AnyMismatch]]:
        yield from self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).to_mismatch_classes(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )

    __slots__ = ('_expression_builder_index',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {ZeroOrMoreExpressionBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

    @override
    def __new__(cls, expression_builder_index: int, /) -> Self:
        _validate_expression_builder_index(expression_builder_index)
        self = super().__new__(cls)
        self._expression_builder_index = expression_builder_index
        return self

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression_builder_index!r})'


class ZeroRepetitionRangeExpressionBuilder(
    ExpressionBuilder[LookaheadMatch | MatchTree, AnyMismatch]
):
    @property
    def expression_builder_index(self, /) -> int:
        return self._expression_builder_index

    @override
    def always_matches(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return True

    @override
    def build(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
    ) -> ZeroRepetitionRangeExpression:
        expression_builder = self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        )
        _check_that_expression_builder_is_progressing(
            expression_builder,
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        )
        return ZeroRepetitionRangeExpression(
            expression_builder.build(
                expression_builders=expression_builders,
                rule_expression_builder_indices=rule_expression_builder_indices,
            ),
            self._end,
        )

    @override
    def is_left_recursive(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).is_left_recursive(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )

    @override
    def is_nullable(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return True

    @override
    def is_terminating(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        is_leftmost: bool,
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> bool:
        return True

    __slots__ = '_end', '_expression_builder_index'

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {ZeroRepetitionRangeExpressionBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

    @override
    def __new__(cls, expression_builder_index: int, end: int, /) -> Self:
        _validate_repetition_expression_builder_bound(end)
        _validate_expression_builder_index(expression_builder_index)
        if end < ZeroRepetitionRangeExpression.MIN_END:
            raise ValueError(
                'Repetition range end should not be '
                f'less than {ZeroRepetitionRangeExpression.MIN_END!r}, '
                f'but got {end!r}.'
            )
        self = super().__new__(cls)
        self._end, self._expression_builder_index = (
            end,
            expression_builder_index,
        )
        return self

    _end: int
    _expression_builder_index: int

    def _get_expression_builder(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
    ) -> ExpressionBuilder[MatchLeaf | MatchTree, AnyMismatch]:
        result = expression_builders[self._expression_builder_index]
        assert _is_expression_builder(
            result,
            expected_match_cls=MatchLeaf | MatchTree,
            expected_mismatch_cls=AnyMismatch,
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ), result
        return result

    @override
    def _to_match_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[LookaheadMatch | MatchTree]]:
        yield LookaheadMatch
        yield MatchTree

    @override
    def _to_mismatch_classes_impl(
        self,
        /,
        *,
        expression_builders: Sequence[
            ExpressionBuilder[AnyMatch, AnyMismatch]
        ],
        rule_expression_builder_indices: Mapping[str, int],
        visited_rule_names: set[str],
    ) -> Iterable[type[AnyMismatch]]:
        yield from self._get_expression_builder(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
        ).to_mismatch_classes(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=visited_rule_names,
        )

    @override
    def __repr__(self, /) -> str:
        return (
            f'{type(self).__qualname__}'
            '('
            f'{self._expression_builder_index!r}, {self._end!r}'
            ')'
        )


def _check_that_expression_builder_is_progressing(
    value: ExpressionBuilder[Any, Any],
    /,
    *,
    expression_builders: Sequence[ExpressionBuilder[AnyMatch, AnyMismatch]],
    rule_expression_builder_indices: Mapping[str, int],
) -> None:
    if value.is_nullable(
        expression_builders=expression_builders,
        rule_expression_builder_indices=rule_expression_builder_indices,
        visited_rule_names=set(),
    ):
        raise ValueError(
            f'Expected progressing expression builder, but got {value!r}.'
        )


def _is_expression_builder(
    value: ExpressionBuilder[AnyMatch, AnyMismatch],
    /,
    *,
    expected_match_cls: type[MatchT_co] | UnionType,
    expected_mismatch_cls: type[MismatchT_co] | UnionType,
    expression_builders: Sequence[ExpressionBuilder[AnyMatch, AnyMismatch]],
    rule_expression_builder_indices: Mapping[str, int],
) -> TypeGuard[ExpressionBuilder[MatchT_co, MismatchT_co]]:
    return all(
        issubclass(match_cls, expected_match_cls)
        for match_cls in value.to_match_classes(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=set(),
        )
    ) and all(
        issubclass(mismatch_cls, expected_mismatch_cls)
        for mismatch_cls in value.to_mismatch_classes(
            expression_builders=expression_builders,
            rule_expression_builder_indices=rule_expression_builder_indices,
            visited_rule_names=set(),
        )
    )


def _validate_expression_builder_index(value: Any, /) -> None:
    if not isinstance(value, int):
        raise TypeError(type(value))
    if value not in range(sys.maxsize + 1):
        raise ValueError(value)


def _validate_repetition_expression_builder_bound(value: Any, /) -> None:
    if not isinstance(value, int):
        raise TypeError(type(value))
