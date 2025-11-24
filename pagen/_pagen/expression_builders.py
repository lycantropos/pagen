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
    Expression,
    NegativeLookaheadExpression,
    OneOrMoreExpression,
    OptionalExpression,
    PositiveLookaheadExpression,
    PrioritizedChoiceExpression,
    RuleReference,
    SequenceExpression,
    SingleQuotedLiteralExpression,
    ZeroOrMoreExpression,
)
from .match import AnyMatch, LookaheadMatch, MatchLeaf, MatchT_co, MatchTree
from .rule import Rule


class ExpressionBuilder(ABC, Generic[MatchT_co]):
    __slots__ = ()

    @abstractmethod
    def build(
        self, /, *, rules: Mapping[str, Rule[Any]]
    ) -> Expression[MatchT_co]:
        raise NotImplementedError

    @abstractmethod
    def is_left_recursive(self, visited_rule_names: set[str], /) -> bool:
        raise NotImplementedError

    def is_lookahead(self, /) -> bool:
        return False

    def to_match_classes(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MatchT_co]]:
        yield from self._to_match_classes_impl(
            visited_rule_names=visited_rule_names
        )

    @abstractmethod
    def _to_match_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MatchT_co]]:
        raise NotImplementedError

    @abstractmethod
    def __repr__(self, /) -> str:
        raise NotImplementedError


@final
class AnyCharacterExpressionBuilder(ExpressionBuilder[MatchLeaf]):
    __slots__ = ()

    @override
    def build(
        self, /, *, rules: Mapping[str, Rule[Any]]
    ) -> AnyCharacterExpression:
        return AnyCharacterExpression()

    @override
    def is_left_recursive(self, visited_rule_names: set[str], /) -> bool:
        return False

    @override
    def _to_match_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MatchLeaf]]:
        yield MatchLeaf

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}()'


@final
class CharacterClassExpressionBuilder(ExpressionBuilder[MatchLeaf]):
    __slots__ = ('_elements',)

    def __new__(
        cls, elements: Sequence[CharacterRange | CharacterSet], /
    ) -> Self:
        assert len(elements) > 0, elements
        self = super().__new__(cls)
        self._elements = merge_consecutive_character_sets(elements)
        return self

    @override
    def build(
        self, /, *, rules: Mapping[str, Rule[Any]]
    ) -> CharacterClassExpression:
        return CharacterClassExpression(self._elements)

    @override
    def is_left_recursive(self, visited_rule_names: set[str], /) -> bool:
        return False

    _elements: Sequence[CharacterRange | CharacterSet]

    @override
    def _to_match_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MatchLeaf]]:
        yield MatchLeaf

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._elements!r})'


@final
class ComplementedCharacterClassExpressionBuilder(
    ExpressionBuilder[MatchLeaf]
):
    __slots__ = ('_elements',)

    def __new__(
        cls, elements: Sequence[CharacterRange | CharacterSet], /
    ) -> Self:
        assert len(elements) > 0, elements
        self = super().__new__(cls)
        self._elements = merge_consecutive_character_sets(elements)
        return self

    @override
    def build(
        self, /, *, rules: Mapping[str, Rule[Any]]
    ) -> ComplementedCharacterClassExpression:
        return ComplementedCharacterClassExpression(self._elements)

    @override
    def is_left_recursive(self, visited_rule_names: set[str], /) -> bool:
        return False

    _elements: Sequence[CharacterRange | CharacterSet]

    @override
    def _to_match_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MatchLeaf]]:
        yield MatchLeaf

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._elements!r})'


class LiteralExpressionBuilder(ExpressionBuilder[MatchLeaf]):
    @property
    @abstractmethod
    def value(self, /) -> str:
        raise NotImplementedError

    @override
    def is_left_recursive(self, visited_rule_names: set[str], /) -> bool:
        return False

    @override
    def _to_match_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MatchLeaf]]:
        yield MatchLeaf

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self.value!r})'


@final
class DoubleQuotedLiteralExpressionBuilder(LiteralExpressionBuilder):
    __slots__ = ('_value',)

    def __new__(cls, value: str, /) -> Self:
        assert len(value) > 0, value
        self = super().__new__(cls)
        self._value = value
        return self

    @override
    def build(
        self, /, *, rules: Mapping[str, Rule[Any]]
    ) -> DoubleQuotedLiteralExpression:
        return DoubleQuotedLiteralExpression(self._value)

    @property
    @override
    def value(self, /) -> str:
        return self._value

    _value: str


@final
class SingleQuotedLiteralExpressionBuilder(LiteralExpressionBuilder):
    __slots__ = ('_value',)

    def __new__(cls, value: str, /) -> Self:
        assert len(value) > 0, value
        self = super().__new__(cls)
        self._value = value
        return self

    @override
    def build(
        self, /, *, rules: Mapping[str, Rule[Any]]
    ) -> SingleQuotedLiteralExpression:
        return SingleQuotedLiteralExpression(self._value)

    @property
    @override
    def value(self, /) -> str:
        return self._value

    _value: str


@final
class NegativeLookaheadExpressionBuilder(ExpressionBuilder[LookaheadMatch]):
    __slots__ = ('_expression_builder',)

    def __new__(
        cls, expression_builder: ExpressionBuilder[MatchLeaf | MatchTree], /
    ) -> Self:
        self = super().__new__(cls)
        self._expression_builder = expression_builder
        return self

    @override
    def build(
        self, /, *, rules: Mapping[str, Rule[Any]]
    ) -> NegativeLookaheadExpression:
        _validate_progressing_expression_builder(self._expression_builder)
        return NegativeLookaheadExpression(
            self._expression_builder.build(rules=rules)
        )

    @override
    def is_lookahead(self, /) -> bool:
        return True

    @override
    def is_left_recursive(self, visited_rule_names: set[str], /) -> bool:
        return self._expression_builder.is_left_recursive(visited_rule_names)

    _expression_builder: ExpressionBuilder[MatchLeaf | MatchTree]

    @override
    def _to_match_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[LookaheadMatch]]:
        yield LookaheadMatch

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression_builder!r})'


@final
class OneOrMoreExpressionBuilder(ExpressionBuilder[MatchTree]):
    __slots__ = ('_expression_builder',)

    def __new__(
        cls, expression_builder: ExpressionBuilder[MatchLeaf | MatchTree], /
    ) -> Self:
        self = super().__new__(cls)
        self._expression_builder = expression_builder
        return self

    @override
    def build(
        self, /, *, rules: Mapping[str, Rule[Any]]
    ) -> OneOrMoreExpression:
        _validate_progressing_expression_builder(self._expression_builder)
        return OneOrMoreExpression(self._expression_builder.build(rules=rules))

    @override
    def is_left_recursive(self, visited_rule_names: set[str], /) -> bool:
        return self._expression_builder.is_left_recursive(visited_rule_names)

    _expression_builder: ExpressionBuilder[MatchLeaf | MatchTree]

    @override
    def _to_match_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MatchTree]]:
        yield MatchTree

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression_builder!r})'


@final
class OptionalExpressionBuilder(ExpressionBuilder[AnyMatch]):
    __slots__ = ('_expression_builder',)

    def __new__(
        cls, expression_builder: ExpressionBuilder[MatchLeaf | MatchTree], /
    ) -> Self:
        self = super().__new__(cls)
        self._expression_builder = expression_builder
        return self

    @override
    def build(
        self, /, *, rules: Mapping[str, Rule[Any]]
    ) -> OptionalExpression:
        _validate_progressing_expression_builder(self._expression_builder)
        return OptionalExpression(self._expression_builder.build(rules=rules))

    @override
    def is_left_recursive(self, visited_rule_names: set[str], /) -> bool:
        return self._expression_builder.is_left_recursive(visited_rule_names)

    _expression_builder: ExpressionBuilder[MatchLeaf | MatchTree]

    @override
    def _to_match_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[AnyMatch]]:
        yield LookaheadMatch
        yield from self._expression_builder.to_match_classes(
            visited_rule_names=visited_rule_names
        )

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression_builder!r})'


@final
class PositiveLookaheadExpressionBuilder(ExpressionBuilder[LookaheadMatch]):
    __slots__ = ('_expression_builder',)

    def __new__(
        cls, expression_builder: ExpressionBuilder[MatchLeaf | MatchTree], /
    ) -> Self:
        self = super().__new__(cls)
        self._expression_builder = expression_builder
        return self

    @override
    def build(
        self, /, *, rules: Mapping[str, Rule[Any]]
    ) -> PositiveLookaheadExpression:
        _validate_progressing_expression_builder(self._expression_builder)
        return PositiveLookaheadExpression(
            self._expression_builder.build(rules=rules)
        )

    @override
    def is_lookahead(self, /) -> bool:
        return True

    @override
    def is_left_recursive(self, visited_rule_names: set[str], /) -> bool:
        return self._expression_builder.is_left_recursive(visited_rule_names)

    _expression_builder: ExpressionBuilder[MatchLeaf | MatchTree]

    @override
    def _to_match_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[LookaheadMatch]]:
        yield LookaheadMatch

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression_builder!r})'


@final
class PrioritizedChoiceExpressionBuilder(ExpressionBuilder[MatchT_co]):
    __slots__ = ('_variant_builders',)

    def __new__(
        cls, variant_builders: Sequence[ExpressionBuilder[MatchT_co]], /
    ) -> Self:
        assert len(variant_builders) > 1, variant_builders
        flattened_variant_builders: list[ExpressionBuilder[MatchT_co]] = []
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

    @property
    def variants(self, /) -> Sequence[ExpressionBuilder[MatchT_co]]:
        return self._variant_builders

    @override
    def build(
        self, /, *, rules: Mapping[str, Rule[Any]]
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

    _variant_builders: Sequence[ExpressionBuilder[MatchT_co]]

    @override
    def _to_match_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MatchT_co]]:
        for variant in self._variant_builders:
            yield from variant.to_match_classes(
                visited_rule_names=visited_rule_names
            )

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._variant_builders!r})'


@final
class RuleReferenceBuilder(ExpressionBuilder[MatchT_co]):
    __slots__ = '_expression_builders', '_name'

    def __new__(
        cls,
        name: str,
        /,
        *,
        expression_builders: Mapping[str, ExpressionBuilder[MatchT_co]],
    ) -> Self:
        assert len(name) > 0, name
        self = super().__new__(cls)
        self._expression_builders, self._name = expression_builders, name
        return self

    @override
    def build(
        self, /, *, rules: Mapping[str, Rule[Any]]
    ) -> RuleReference[MatchT_co]:
        cursor: RuleReferenceBuilder[Any] = self
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

    _expression_builders: Mapping[str, ExpressionBuilder[MatchT_co]]
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
class SequenceExpressionBuilder(ExpressionBuilder[MatchTree]):
    __slots__ = ('_element_builders',)

    def __new__(
        cls, element_builders: Sequence[ExpressionBuilder[AnyMatch]], /
    ) -> Self:
        assert len(element_builders) > 1, element_builders
        self = super().__new__(cls)
        self._element_builders = element_builders
        return self

    @override
    def build(
        self, /, *, rules: Mapping[str, Rule[Any]]
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
            if element_builder.is_lookahead():
                if element_builder.is_left_recursive(visited_rule_names):
                    return True
                continue
            return element_builder.is_left_recursive(visited_rule_names)
        raise ValueError('Sequence consists of non-left recursive lookaheads.')

    _element_builders: Sequence[ExpressionBuilder[AnyMatch]]

    @override
    def _to_match_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[MatchTree]]:
        yield MatchTree

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._element_builders!r})'


@final
class ZeroOrMoreExpressionBuilder(
    ExpressionBuilder[LookaheadMatch | MatchTree]
):
    __slots__ = ('_expression_builder',)

    def __new__(
        cls, expression_builder: ExpressionBuilder[MatchLeaf | MatchTree], /
    ) -> Self:
        self = super().__new__(cls)
        self._expression_builder = expression_builder
        return self

    @override
    def build(
        self, /, *, rules: Mapping[str, Rule[Any]]
    ) -> ZeroOrMoreExpression:
        _validate_progressing_expression_builder(self._expression_builder)
        return ZeroOrMoreExpression(
            self._expression_builder.build(rules=rules)
        )

    @override
    def is_left_recursive(self, visited_rule_names: set[str], /) -> bool:
        return self._expression_builder.is_left_recursive(visited_rule_names)

    _expression_builder: ExpressionBuilder[MatchLeaf | MatchTree]

    @override
    def _to_match_classes_impl(
        self, /, *, visited_rule_names: set[str]
    ) -> Iterable[type[LookaheadMatch | MatchTree]]:
        yield LookaheadMatch
        yield MatchTree

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression_builder!r})'


def _is_progressing_expression_builder(
    expression_builder: ExpressionBuilder[Any], /
) -> TypeIs[ExpressionBuilder[MatchLeaf | MatchTree]]:
    return not any(
        issubclass(match_cls, LookaheadMatch)
        for match_cls in (
            expression_builder.to_match_classes(visited_rule_names=set())
        )
    )


def _validate_progressing_expression_builder(
    expression_builder: ExpressionBuilder[Any], /
) -> None:
    if not _is_progressing_expression_builder(expression_builder):
        raise ValueError(expression_builder)
