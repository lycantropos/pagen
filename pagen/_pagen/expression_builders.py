from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Generic, final

from typing_extensions import Self, TypeIs, override

from . import CharacterRange, CharacterSet
from .character_containers import merge_consecutive_character_sets
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
from .mismatch import (
    AnyMismatch,
    MismatchLeaf,
    MismatchT_co,
    MismatchTree,
    NoMismatch,
)
from .rule import Rule


class ExpressionBuilder(ABC, Generic[MatchT_co, MismatchT_co]):
    @abstractmethod
    def build(
        self, /, *, rules: Mapping[str, Rule[Any, Any]]
    ) -> Expression[MatchT_co, MismatchT_co]:
        raise NotImplementedError

    @abstractmethod
    def is_left_recursive(self, visited_rule_names: set[str], /) -> bool:
        raise NotImplementedError

    @abstractmethod
    def is_terminating(self, visited_rule_names: set[str], /) -> bool:
        raise NotImplementedError

    def to_match_classes(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MatchT_co]]:
        yield from self._to_match_classes_impl(
            visited_rule_names=visited_rule_names
        )

    def to_mismatch_classes(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MismatchT_co]]:
        yield from self._to_mismatch_classes_impl(
            visited_rule_names=visited_rule_names
        )

    __slots__ = ()

    @abstractmethod
    def _to_match_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MatchT_co]]:
        raise NotImplementedError

    @abstractmethod
    def _to_mismatch_classes_impl(
        self, /, *, visited_rule_names: set[str]
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
    def build(
        self, /, *, rules: Mapping[str, Rule[Any, Any]]
    ) -> AnyCharacterExpression:
        return AnyCharacterExpression()

    @override
    def is_left_recursive(self, visited_rule_names: set[str], /) -> bool:
        return False

    @override
    def is_terminating(self, visited_rule_names: set[str], /) -> bool:
        return True

    __slots__ = ()

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {AnyCharacterExpressionBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

    @override
    def _to_match_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MatchLeaf]]:
        yield MatchLeaf

    @override
    def _to_mismatch_classes_impl(
        self, /, *, visited_rule_names: set[str]
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
    def build(
        self, /, *, rules: Mapping[str, Rule[Any, Any]]
    ) -> CharacterClassExpression:
        return CharacterClassExpression(self._elements)

    @override
    def is_left_recursive(self, visited_rule_names: set[str], /) -> bool:
        return False

    @override
    def is_terminating(self, visited_rule_names: set[str], /) -> bool:
        return True

    __slots__ = ('_elements',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {CharacterClassExpressionBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

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
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MatchLeaf]]:
        yield MatchLeaf

    @override
    def _to_mismatch_classes_impl(
        self, /, *, visited_rule_names: set[str]
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
    def build(
        self, /, *, rules: Mapping[str, Rule[Any, Any]]
    ) -> ComplementedCharacterClassExpression:
        return ComplementedCharacterClassExpression(self._elements)

    @override
    def is_left_recursive(self, visited_rule_names: set[str], /) -> bool:
        return False

    @override
    def is_terminating(self, visited_rule_names: set[str], /) -> bool:
        return True

    __slots__ = ('_elements',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            'type '
            f'{ComplementedCharacterClassExpressionBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

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
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MatchLeaf]]:
        yield MatchLeaf

    @override
    def _to_mismatch_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MismatchLeaf]]:
        yield MismatchLeaf

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._elements!r})'


@final
class ExactRepetitionExpressionBuilder(
    ExpressionBuilder[MatchTree, MismatchTree]
):
    @override
    def build(
        self, /, *, rules: Mapping[str, Rule[Any, Any]]
    ) -> ExactRepetitionExpression:
        _check_that_expression_builder_is_progressing(self._expression_builder)
        return ExactRepetitionExpression(
            self._expression_builder.build(rules=rules), self._count
        )

    @override
    def is_left_recursive(self, visited_rule_names: set[str], /) -> bool:
        return self._expression_builder.is_left_recursive(visited_rule_names)

    @override
    def is_terminating(self, visited_rule_names: set[str], /) -> bool:
        return self._expression_builder.is_terminating(visited_rule_names)

    __slots__ = '_count', '_expression_builder'

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {ExactRepetitionExpressionBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls,
        expression_builder: ExpressionBuilder[
            MatchLeaf | MatchTree, AnyMismatch
        ],
        count: int,
        /,
    ) -> Self:
        _validate_repetition_expression_builder_bound(count)
        _validate_expression_builder(expression_builder)
        if count < ExactRepetitionExpression.MIN_COUNT:
            raise ValueError(
                'Repetition count should not be '
                f'less than {ExactRepetitionExpression.MIN_COUNT!r}, '
                f'but got {count!r}.'
            )
        self = super().__new__(cls)
        self._count, self._expression_builder = count, expression_builder
        return self

    @override
    def _to_match_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MatchTree]]:
        yield MatchTree

    @override
    def _to_mismatch_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MismatchTree]]:
        yield MismatchTree

    _count: int
    _expression_builder: ExpressionBuilder[MatchLeaf | MatchTree, AnyMismatch]

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression_builder!r})'


class LiteralExpressionBuilder(ExpressionBuilder[MatchLeaf, MismatchLeaf]):
    @override
    def is_left_recursive(self, visited_rule_names: set[str], /) -> bool:
        return False

    @override
    def is_terminating(self, visited_rule_names: set[str], /) -> bool:
        return True

    __slots__ = ()

    @override
    def _to_match_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MatchLeaf]]:
        yield MatchLeaf

    @override
    def _to_mismatch_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MismatchLeaf]]:
        yield MismatchLeaf


@final
class DoubleQuotedLiteralExpressionBuilder(LiteralExpressionBuilder):
    @override
    def build(
        self, /, *, rules: Mapping[str, Rule[Any, Any]]
    ) -> DoubleQuotedLiteralExpression:
        return DoubleQuotedLiteralExpression(self._value)

    __slots__ = ('_value',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {DoubleQuotedLiteralExpressionBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

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
        self, /, *, rules: Mapping[str, Rule[Any, Any]]
    ) -> SingleQuotedLiteralExpression:
        return SingleQuotedLiteralExpression(self._value)

    __slots__ = ('_value',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {SingleQuotedLiteralExpressionBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

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
    ExpressionBuilder[LookaheadMatch, MismatchTree]
):
    @override
    def build(
        self, /, *, rules: Mapping[str, Rule[Any, Any]]
    ) -> NegativeLookaheadExpression:
        _check_that_expression_builder_is_progressing(self._expression_builder)
        return NegativeLookaheadExpression(
            self._expression_builder.build(rules=rules)
        )

    @override
    def is_left_recursive(self, visited_rule_names: set[str], /) -> bool:
        return self._expression_builder.is_left_recursive(visited_rule_names)

    @override
    def is_terminating(self, visited_rule_names: set[str], /) -> bool:
        return self._expression_builder.is_terminating(visited_rule_names)

    __slots__ = ('_expression_builder',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {NegativeLookaheadExpressionBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls,
        expression_builder: ExpressionBuilder[
            MatchLeaf | MatchTree, AnyMismatch
        ],
        /,
    ) -> Self:
        _validate_expression_builder(expression_builder)
        self = super().__new__(cls)
        self._expression_builder = expression_builder
        return self

    _expression_builder: ExpressionBuilder[MatchLeaf | MatchTree, AnyMismatch]

    @override
    def _to_match_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[LookaheadMatch]]:
        yield LookaheadMatch

    @override
    def _to_mismatch_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MismatchTree]]:
        yield MismatchTree

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression_builder!r})'


@final
class OneOrMoreExpressionBuilder(ExpressionBuilder[MatchTree, MismatchTree]):
    @override
    def build(
        self, /, *, rules: Mapping[str, Rule[Any, Any]]
    ) -> OneOrMoreExpression:
        _check_that_expression_builder_is_progressing(self._expression_builder)
        return OneOrMoreExpression(self._expression_builder.build(rules=rules))

    @override
    def is_left_recursive(self, visited_rule_names: set[str], /) -> bool:
        return self._expression_builder.is_left_recursive(visited_rule_names)

    @override
    def is_terminating(self, visited_rule_names: set[str], /) -> bool:
        return self._expression_builder.is_terminating(visited_rule_names)

    __slots__ = ('_expression_builder',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {OneOrMoreExpressionBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls,
        expression_builder: ExpressionBuilder[
            MatchLeaf | MatchTree, AnyMismatch
        ],
        /,
    ) -> Self:
        _validate_expression_builder(expression_builder)
        self = super().__new__(cls)
        self._expression_builder = expression_builder
        return self

    _expression_builder: ExpressionBuilder[MatchLeaf | MatchTree, AnyMismatch]

    @override
    def _to_match_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MatchTree]]:
        yield MatchTree

    @override
    def _to_mismatch_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MismatchTree]]:
        yield MismatchTree

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression_builder!r})'


@final
class OptionalExpressionBuilder(ExpressionBuilder[AnyMatch, NoMismatch]):
    @override
    def build(
        self, /, *, rules: Mapping[str, Rule[Any, Any]]
    ) -> OptionalExpression:
        _check_that_expression_builder_is_progressing(self._expression_builder)
        return OptionalExpression(self._expression_builder.build(rules=rules))

    @override
    def is_left_recursive(self, visited_rule_names: set[str], /) -> bool:
        return self._expression_builder.is_left_recursive(visited_rule_names)

    @override
    def is_terminating(self, visited_rule_names: set[str], /) -> bool:
        return self._expression_builder.is_terminating(visited_rule_names)

    __slots__ = ('_expression_builder',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {OptionalExpressionBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls,
        expression_builder: ExpressionBuilder[
            MatchLeaf | MatchTree, AnyMismatch
        ],
        /,
    ) -> Self:
        _validate_expression_builder(expression_builder)
        self = super().__new__(cls)
        self._expression_builder = expression_builder
        return self

    _expression_builder: ExpressionBuilder[MatchLeaf | MatchTree, AnyMismatch]

    @override
    def _to_match_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[AnyMatch]]:
        yield LookaheadMatch
        yield from self._expression_builder.to_match_classes(
            visited_rule_names=visited_rule_names
        )

    @override
    def _to_mismatch_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[NoMismatch]]:
        yield from ()

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression_builder!r})'


@final
class PositiveLookaheadExpressionBuilder(
    ExpressionBuilder[LookaheadMatch, MismatchTree]
):
    @override
    def build(
        self, /, *, rules: Mapping[str, Rule[Any, Any]]
    ) -> PositiveLookaheadExpression:
        _check_that_expression_builder_is_progressing(self._expression_builder)
        return PositiveLookaheadExpression(
            self._expression_builder.build(rules=rules)
        )

    @override
    def is_left_recursive(self, visited_rule_names: set[str], /) -> bool:
        return self._expression_builder.is_left_recursive(visited_rule_names)

    @override
    def is_terminating(self, visited_rule_names: set[str], /) -> bool:
        return self._expression_builder.is_terminating(visited_rule_names)

    __slots__ = ('_expression_builder',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {PositiveLookaheadExpressionBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls,
        expression_builder: ExpressionBuilder[
            MatchLeaf | MatchTree, AnyMismatch
        ],
        /,
    ) -> Self:
        self = super().__new__(cls)
        self._expression_builder = expression_builder
        return self

    _expression_builder: ExpressionBuilder[MatchLeaf | MatchTree, AnyMismatch]

    @override
    def _to_match_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[LookaheadMatch]]:
        yield LookaheadMatch

    @override
    def _to_mismatch_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MismatchTree]]:
        yield MismatchTree

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression_builder!r})'


@final
class PositiveOrMoreExpressionBuilder(
    ExpressionBuilder[MatchTree, MismatchTree]
):
    @override
    def build(
        self, /, *, rules: Mapping[str, Rule[Any, Any]]
    ) -> PositiveOrMoreExpression:
        _check_that_expression_builder_is_progressing(self._expression_builder)
        return PositiveOrMoreExpression(
            self._expression_builder.build(rules=rules), self._start
        )

    @override
    def is_left_recursive(self, visited_rule_names: set[str], /) -> bool:
        return self._expression_builder.is_left_recursive(visited_rule_names)

    @override
    def is_terminating(self, visited_rule_names: set[str], /) -> bool:
        return self._expression_builder.is_terminating(visited_rule_names)

    __slots__ = '_expression_builder', '_start'

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {PositiveOrMoreExpressionBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls,
        expression_builder: ExpressionBuilder[
            MatchLeaf | MatchTree, AnyMismatch
        ],
        start: int,
        /,
    ) -> Self:
        _validate_repetition_expression_builder_bound(start)
        _validate_expression_builder(expression_builder)
        if start < PositiveOrMoreExpression.MIN_START:
            raise ValueError(
                'Repetition start should not be '
                f'less than {PositiveOrMoreExpression.MIN_START!r}, '
                f'but got {start!r}.'
            )
        self = super().__new__(cls)
        self._expression_builder, self._start = expression_builder, start
        return self

    _expression_builder: ExpressionBuilder[MatchLeaf | MatchTree, AnyMismatch]
    _start: int

    @override
    def _to_match_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MatchTree]]:
        yield MatchTree

    @override
    def _to_mismatch_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MismatchTree]]:
        yield MismatchTree

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression_builder!r})'


@final
class PositiveRepetitionRangeExpressionBuilder(
    ExpressionBuilder[MatchTree, MismatchTree]
):
    def build(
        self, /, *, rules: Mapping[str, Rule[Any, Any]]
    ) -> PositiveRepetitionRangeExpression:
        _check_that_expression_builder_is_progressing(self._expression_builder)
        return PositiveRepetitionRangeExpression(
            self._expression_builder.build(rules=rules), self._start, self._end
        )

    def is_left_recursive(self, visited_rule_names: set[str], /) -> bool:
        return self._expression_builder.is_left_recursive(visited_rule_names)

    @override
    def is_terminating(self, visited_rule_names: set[str], /) -> bool:
        return self._expression_builder.is_terminating(visited_rule_names)

    __slots__ = '_end', '_expression_builder', '_start'

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {PositiveRepetitionRangeExpressionBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls,
        expression_builder: ExpressionBuilder[
            MatchLeaf | MatchTree, AnyMismatch
        ],
        start: int,
        end: int,
        /,
    ) -> Self:
        _validate_repetition_expression_builder_bound(start)
        _validate_repetition_expression_builder_bound(end)
        _validate_expression_builder(expression_builder)
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
        self._expression_builder, self._end, self._start = (
            expression_builder,
            end,
            start,
        )
        return self

    _end: int
    _expression_builder: ExpressionBuilder[MatchLeaf | MatchTree, AnyMismatch]
    _start: int

    @override
    def _to_match_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MatchTree]]:
        yield MatchTree

    @override
    def _to_mismatch_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MismatchTree]]:
        yield MismatchTree

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression_builder!r})'


@final
class PrioritizedChoiceExpressionBuilder(
    ExpressionBuilder[MatchT_co, MismatchTree]
):
    @override
    def build(
        self, /, *, rules: Mapping[str, Rule[Any, Any]]
    ) -> PrioritizedChoiceExpression[MatchT_co]:
        return PrioritizedChoiceExpression(
            [
                variant_builder.build(rules=rules)
                for variant_builder in self._variant_builders
            ]
        )

    @override
    def is_left_recursive(self, visited_rule_names: set[str], /) -> bool:
        return any(
            variant_builder.is_left_recursive(visited_rule_names)
            for variant_builder in self._variant_builders
        )

    @override
    def is_terminating(self, visited_rule_names: set[str], /) -> bool:
        return any(
            variant_builder.is_terminating(visited_rule_names)
            for variant_builder in self._variant_builders
        )

    __slots__ = ('_variant_builders',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {PrioritizedChoiceExpressionBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls,
        variant_builders: Sequence[ExpressionBuilder[MatchT_co, AnyMismatch]],
        /,
    ) -> Self:
        assert len(variant_builders) > 1, variant_builders
        flattened_variant_builders: list[
            ExpressionBuilder[MatchT_co, AnyMismatch]
        ] = []
        for variant_builder in variant_builders:
            if isinstance(variant_builder, PrioritizedChoiceExpressionBuilder):
                flattened_variant_builders.extend(
                    variant_builder._variant_builders  # noqa: SLF001
                )
            else:
                flattened_variant_builders.append(variant_builder)
        self = super().__new__(cls)
        self._variant_builders = flattened_variant_builders
        return self

    _variant_builders: Sequence[ExpressionBuilder[MatchT_co, AnyMismatch]]

    @override
    def _to_match_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MatchT_co]]:
        for variant in self._variant_builders:
            yield from variant.to_match_classes(
                visited_rule_names=visited_rule_names
            )

    @override
    def _to_mismatch_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MismatchTree]]:
        yield MismatchTree

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._variant_builders!r})'


@final
class RuleReferenceBuilder(ExpressionBuilder[MatchT_co, MismatchT_co]):
    @override
    def build(
        self, /, *, rules: Mapping[str, Rule[Any, Any]]
    ) -> RuleReference[MatchT_co, MismatchT_co]:
        cursor: RuleReferenceBuilder[Any, Any] = self
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
                candidate = self._expression_builders[cursor._name]
            except KeyError:
                raise ValueError(
                    f'Name {cursor_name!r} is not found in rules.'
                ) from None
            if not isinstance(candidate, RuleReferenceBuilder):
                return RuleReference(
                    self._name,
                    cursor_name,
                    match_classes=list(
                        candidate.to_match_classes(visited_rule_names=set())
                    ),
                    mismatch_classes=list(
                        candidate.to_mismatch_classes(visited_rule_names=set())
                    ),
                    rules=rules,
                )
            cursor = candidate

    @override
    def is_left_recursive(self, visited_rule_names: set[str], /) -> bool:
        if self._name in visited_rule_names:
            return True
        visited_rule_names.add(self._name)
        result = self._expression_builders[self._name].is_left_recursive(
            visited_rule_names
        )
        visited_rule_names.remove(self._name)
        return result

    @override
    def is_terminating(self, visited_rule_names: set[str], /) -> bool:
        if self._name in visited_rule_names:
            return False
        visited_rule_names.add(self._name)
        result = self._expression_builders[self._name].is_terminating(
            visited_rule_names
        )
        visited_rule_names.remove(self._name)
        return result

    __slots__ = '_expression_builders', '_name'

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {RuleReferenceBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls,
        name: str,
        /,
        *,
        expression_builders: Mapping[
            str, ExpressionBuilder[MatchT_co, MismatchT_co]
        ],
    ) -> Self:
        assert len(name) > 0, name
        self = super().__new__(cls)
        self._expression_builders, self._name = expression_builders, name
        return self

    _expression_builders: Mapping[
        str, ExpressionBuilder[MatchT_co, MismatchT_co]
    ]
    _name: str

    @override
    def _to_match_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MatchT_co]]:
        if self._name in visited_rule_names:
            return
        visited_rule_names.add(self._name)
        yield from self._expression_builders[self._name].to_match_classes(
            visited_rule_names=visited_rule_names
        )
        visited_rule_names.remove(self._name)

    @override
    def _to_mismatch_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MismatchT_co]]:
        if self._name in visited_rule_names:
            return
        visited_rule_names.add(self._name)
        yield from self._expression_builders[self._name].to_mismatch_classes(
            visited_rule_names=visited_rule_names
        )
        visited_rule_names.remove(self._name)

    @override
    def __repr__(self, /) -> str:
        return (
            f'{type(self).__qualname__}'
            '('
            f'{self._name!r}, '
            f'expression_builders={self._expression_builders!r}'
            ')'
        )


@final
class SequenceExpressionBuilder(ExpressionBuilder[MatchTree, MismatchTree]):
    @override
    def build(
        self, /, *, rules: Mapping[str, Rule[Any, Any]]
    ) -> SequenceExpression:
        if not any(
            _is_progressing_expression_builder(element_builder)
            for element_builder in self._element_builders
        ):
            raise ValueError(self._element_builders)
        return SequenceExpression(
            [
                element_builder.build(rules=rules)
                for element_builder in self._element_builders
            ]
        )

    @override
    def is_left_recursive(self, visited_rule_names: set[str], /) -> bool:
        for element_builder in self._element_builders:
            if isinstance(
                element_builder,
                (
                    NegativeLookaheadExpressionBuilder
                    | PositiveLookaheadExpressionBuilder
                ),
            ):
                if element_builder.is_left_recursive(visited_rule_names):
                    return True
                continue
            return element_builder.is_left_recursive(visited_rule_names)
        raise ValueError('Sequence consists of non-left recursive lookaheads.')

    @override
    def is_terminating(self, visited_rule_names: set[str], /) -> bool:
        return all(
            element_builder.is_terminating(visited_rule_names)
            for element_builder in self._element_builders
        )

    __slots__ = ('_element_builders',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {SequenceExpressionBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls,
        element_builders: Sequence[ExpressionBuilder[AnyMatch, AnyMismatch]],
        /,
    ) -> Self:
        assert len(element_builders) > 1, element_builders
        self = super().__new__(cls)
        self._element_builders = element_builders
        return self

    _element_builders: Sequence[ExpressionBuilder[AnyMatch, AnyMismatch]]

    @override
    def _to_match_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MatchTree]]:
        yield MatchTree

    @override
    def _to_mismatch_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MismatchTree]]:
        yield MismatchTree

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._element_builders!r})'


@final
class ZeroOrMoreExpressionBuilder(
    ExpressionBuilder[LookaheadMatch | MatchTree, NoMismatch]
):
    @override
    def build(
        self, /, *, rules: Mapping[str, Rule[Any, Any]]
    ) -> ZeroOrMoreExpression:
        _check_that_expression_builder_is_progressing(self._expression_builder)
        return ZeroOrMoreExpression(
            self._expression_builder.build(rules=rules)
        )

    @override
    def is_left_recursive(self, visited_rule_names: set[str], /) -> bool:
        return self._expression_builder.is_left_recursive(visited_rule_names)

    @override
    def is_terminating(self, visited_rule_names: set[str], /) -> bool:
        return self._expression_builder.is_terminating(visited_rule_names)

    __slots__ = ('_expression_builder',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {ZeroOrMoreExpressionBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls,
        expression_builder: ExpressionBuilder[
            MatchLeaf | MatchTree, AnyMismatch
        ],
        /,
    ) -> Self:
        _validate_expression_builder(expression_builder)
        self = super().__new__(cls)
        self._expression_builder = expression_builder
        return self

    _expression_builder: ExpressionBuilder[MatchLeaf | MatchTree, AnyMismatch]

    @override
    def _to_match_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[LookaheadMatch | MatchTree]]:
        yield LookaheadMatch
        yield MatchTree

    @override
    def _to_mismatch_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[NoMismatch]]:
        yield from ()

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression_builder!r})'


class ZeroRepetitionRangeExpressionBuilder(
    ExpressionBuilder[LookaheadMatch | MatchTree, NoMismatch]
):
    def build(
        self, /, *, rules: Mapping[str, Rule[Any, Any]]
    ) -> ZeroRepetitionRangeExpression:
        _check_that_expression_builder_is_progressing(self._expression_builder)
        return ZeroRepetitionRangeExpression(
            self._expression_builder.build(rules=rules), self._end
        )

    def is_left_recursive(self, visited_rule_names: set[str], /) -> bool:
        return self._expression_builder.is_left_recursive(visited_rule_names)

    @override
    def is_terminating(self, visited_rule_names: set[str], /) -> bool:
        return self._expression_builder.is_terminating(visited_rule_names)

    __slots__ = '_end', '_expression_builder'

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {ZeroRepetitionRangeExpressionBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls,
        expression_builder: ExpressionBuilder[
            MatchLeaf | MatchTree, AnyMismatch
        ],
        end: int,
        /,
    ) -> Self:
        _validate_repetition_expression_builder_bound(end)
        _validate_expression_builder(expression_builder)
        if end < ZeroRepetitionRangeExpression.MIN_END:
            raise ValueError(
                'Repetition range end should not be '
                f'less than {ZeroRepetitionRangeExpression.MIN_END!r}, '
                f'but got {end!r}.'
            )
        self = super().__new__(cls)
        self._end, self._expression_builder = end, expression_builder
        return self

    _end: int
    _expression_builder: ExpressionBuilder[MatchLeaf | MatchTree, AnyMismatch]

    @override
    def _to_match_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[LookaheadMatch | MatchTree]]:
        yield LookaheadMatch
        yield MatchTree

    @override
    def _to_mismatch_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[NoMismatch]]:
        yield from ()

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression_builder!r})'


def _check_that_expression_builder_is_progressing(
    value: ExpressionBuilder[Any, Any], /
) -> None:
    if not _is_progressing_expression_builder(value):
        raise ValueError(
            f'Expected progressing expression builder, but got {value!r}.'
        )


def _is_progressing_expression_builder(
    value: ExpressionBuilder[Any, Any], /
) -> TypeIs[ExpressionBuilder[MatchLeaf | MatchTree, AnyMismatch]]:
    return not any(
        issubclass(match_cls, LookaheadMatch)
        for match_cls in value.to_match_classes(visited_rule_names=set())
    )


def _validate_expression_builder(value: Any, /) -> None:
    if not isinstance(value, ExpressionBuilder):
        raise TypeError(type(value))


def _validate_repetition_expression_builder_bound(value: Any, /) -> None:
    if not isinstance(value, int):
        raise TypeError(type(value))
