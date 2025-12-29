from __future__ import annotations

from collections.abc import Sequence
from functools import singledispatch

from typing_extensions import override

from .character_containers import CharacterRange, CharacterSet
from .expression_builders import (
    AnyCharacterExpressionBuilder,
    CharacterClassExpressionBuilder,
    ComplementedCharacterClassExpressionBuilder,
    DoubleQuotedLiteralExpressionBuilder,
    ExactRepetitionExpressionBuilder,
    ExpressionBuilder,
    NegativeLookaheadExpressionBuilder,
    OneOrMoreExpressionBuilder,
    OptionalExpressionBuilder,
    PositiveLookaheadExpressionBuilder,
    PositiveOrMoreExpressionBuilder,
    PositiveRepetitionRangeExpressionBuilder,
    PrioritizedChoiceExpressionBuilder,
    RuleReferenceBuilder,
    SequenceExpressionBuilder,
    SingleQuotedLiteralExpressionBuilder,
    ZeroOrMoreExpressionBuilder,
    ZeroRepetitionRangeExpressionBuilder,
)
from .grammar import Grammar
from .match import AnyMatch
from .mismatch import AnyMismatch
from .rule import LeftRecursiveRule, NonLeftRecursiveRule


class GrammarBuilder:
    def add_rule(self, name: str, expression_builder_index: int, /) -> None:
        expression_builder_index_range = range(len(self._expression_builders))
        if expression_builder_index not in expression_builder_index_range:
            raise ValueError(
                'Expression builder index is out of range: '
                f'{expression_builder_index!r} is not '
                f'in {expression_builder_index_range!r}.'
            )
        if (
            existing_expression_builder_index := (
                self._rule_expression_builder_indices.get(name)
            )
        ) is not None:
            existing_expression_builder = self._expression_builders[
                existing_expression_builder_index
            ]
            expression_builder = self._expression_builders[
                expression_builder_index
            ]
            raise ValueError(
                f'Rule redefinition is not allowed, '
                f'but for {name!r} tried to replace '
                f'{existing_expression_builder!r} '
                f'with {expression_builder!r}.'
            )
        self._rule_expression_builder_indices[name] = expression_builder_index

    def any_character_expression(self, /) -> int:
        return self._register_expression_builder(
            AnyCharacterExpressionBuilder()
        )

    def build(self, /) -> Grammar:
        self._validate()
        return self._build()

    def character_class_expression(
        self, elements: Sequence[CharacterRange | CharacterSet], /
    ) -> int:
        return self._register_expression_builder(
            CharacterClassExpressionBuilder(elements)
        )

    def complemented_character_class_expression(
        self, elements: Sequence[CharacterRange | CharacterSet], /
    ) -> int:
        return self._register_expression_builder(
            ComplementedCharacterClassExpressionBuilder(elements)
        )

    def double_quoted_literal_expression(self, value: str, /) -> int:
        return self._register_expression_builder(
            DoubleQuotedLiteralExpressionBuilder(value)
        )

    def exact_repetition_expression(
        self, expression_builder_index: int, count: int, /
    ) -> int:
        return self._register_expression_builder(
            ExactRepetitionExpressionBuilder(expression_builder_index, count)
        )

    def negative_lookahead_expression(
        self, expression_builder_index: int, /
    ) -> int:
        return self._register_expression_builder(
            NegativeLookaheadExpressionBuilder(expression_builder_index)
        )

    def one_or_more_expression(self, expression_builder_index: int, /) -> int:
        return self._register_expression_builder(
            OneOrMoreExpressionBuilder(expression_builder_index)
        )

    def optional_expression(self, expression_builder_index: int, /) -> int:
        return self._register_expression_builder(
            OptionalExpressionBuilder(expression_builder_index)
        )

    def positive_lookahead_expression(
        self, expression_builder_index: int, /
    ) -> int:
        return self._register_expression_builder(
            PositiveLookaheadExpressionBuilder(expression_builder_index)
        )

    def positive_or_more_expression(
        self, expression_builder_index: int, start: int, /
    ) -> int:
        return self._register_expression_builder(
            PositiveOrMoreExpressionBuilder(expression_builder_index, start)
        )

    def positive_repetition_range_expression(
        self, expression_builder_index: int, start: int, end: int, /
    ) -> int:
        return self._register_expression_builder(
            PositiveRepetitionRangeExpressionBuilder(
                expression_builder_index, start, end
            )
        )

    def prioritized_choice_expression(
        self, variant_builder_indices: Sequence[int], /
    ) -> int:
        return self._register_expression_builder(
            PrioritizedChoiceExpressionBuilder(variant_builder_indices)
        )

    def rule_reference(self, name: str, /) -> int:
        return self._register_expression_builder(RuleReferenceBuilder(name))

    def sequence_expression(
        self, element_builder_indices: Sequence[int], /
    ) -> int:
        return self._register_expression_builder(
            SequenceExpressionBuilder(element_builder_indices)
        )

    def single_quoted_literal_expression(self, value: str, /) -> int:
        return self._register_expression_builder(
            SingleQuotedLiteralExpressionBuilder(value)
        )

    def zero_or_more_expression(self, expression_builder_index: int, /) -> int:
        return self._register_expression_builder(
            ZeroOrMoreExpressionBuilder(expression_builder_index)
        )

    def zero_repetition_range_expression(
        self, expression_builder_index: int, end: int, /
    ) -> int:
        return self._register_expression_builder(
            ZeroRepetitionRangeExpressionBuilder(expression_builder_index, end)
        )

    _expression_builders: list[ExpressionBuilder[AnyMatch, AnyMismatch]]
    _rule_expression_builder_indices: dict[str, int]

    def _build(self, /) -> Grammar:
        return Grammar(
            {
                rule_name: (
                    LeftRecursiveRule
                    if (
                        rule_expression_builder := self._expression_builders[
                            rule_expression_builder_index
                        ]
                    ).is_left_recursive(
                        expression_builders=self._expression_builders,
                        rule_expression_builder_indices=(
                            self._rule_expression_builder_indices
                        ),
                        visited_rule_names=set(),
                    )
                    else NonLeftRecursiveRule
                )(
                    rule_name,
                    rule_expression_builder.build(
                        expression_builders=self._expression_builders,
                        rule_expression_builder_indices=(
                            self._rule_expression_builder_indices
                        ),
                    ),
                )
                for (
                    rule_name,
                    rule_expression_builder_index,
                ) in self._rule_expression_builder_indices.items()
            }
        )

    def _register_expression_builder(
        self, expression_builder: ExpressionBuilder[AnyMatch, AnyMismatch], /
    ) -> int:
        result = len(self._expression_builders)
        self._expression_builders.append(expression_builder)
        return result

    def _validate(self, /) -> None:
        if (
            len(
                non_terminating_rules := [
                    rule_name
                    for rule_name, rule_expression_builder_index in (
                        self._rule_expression_builder_indices.items()
                    )
                    if not self._expression_builders[
                        rule_expression_builder_index
                    ].is_terminating(
                        expression_builders=self._expression_builders,
                        is_leftmost=True,
                        rule_expression_builder_indices=(
                            self._rule_expression_builder_indices
                        ),
                        visited_rule_names=set(),
                    )
                ]
            )
            > 0
        ):
            non_terminating_rules.sort()
            raise ValueError(
                'All rules should be terminating, '
                'but the following ones are not: '
                f'{", ".join(map(repr, non_terminating_rules))}.'
            )
        used_expression_builder_indices = [False] * len(
            self._expression_builders
        )
        for (
            rule_expression_builder_index
        ) in self._rule_expression_builder_indices.values():
            used_expression_builder_indices[rule_expression_builder_index] = (
                True
            )
            _walk_expression_builder(
                self._expression_builders[rule_expression_builder_index],
                expression_builders=self._expression_builders,
                used_expression_builder_indices=(
                    used_expression_builder_indices
                ),
            )
        if not all(used_expression_builder_indices):
            unused_expression_builders = [
                self._expression_builders[index]
                for index, used in enumerate(used_expression_builder_indices)
                if not used
            ]
            raise ValueError(
                'All expression builders should be used in rules, '
                f'but got: {unused_expression_builders!r}.'
            )

    __slots__ = '_expression_builders', '_rule_expression_builder_indices'

    def __init__(
        self,
        expression_builders: (
            list[ExpressionBuilder[AnyMatch, AnyMismatch]] | None
        ) = None,
        rule_expression_indices: dict[str, int] | None = None,
        /,
    ) -> None:
        if not isinstance(expression_builders, list | None):
            raise TypeError(type(expression_builders))
        if not isinstance(rule_expression_indices, dict | None):
            raise TypeError(type(rule_expression_indices))
        self._expression_builders = expression_builders or []
        self._rule_expression_builder_indices = rule_expression_indices or {}

    @override
    def __repr__(self, /) -> str:
        return (
            f'{type(self).__qualname__}'
            '('
            f'{self._expression_builders!r}, '
            f'{self._rule_expression_builder_indices!r}'
            ')'
        )


@singledispatch
def _walk_expression_builder(
    expression_builder: ExpressionBuilder[AnyMatch, AnyMismatch],
    /,
    *,
    expression_builders: Sequence[ExpressionBuilder[AnyMatch, AnyMismatch]],
    used_expression_builder_indices: list[bool],
) -> None:
    raise TypeError(type(expression_builder))


@_walk_expression_builder.register(AnyCharacterExpressionBuilder)
@_walk_expression_builder.register(CharacterClassExpressionBuilder)
@_walk_expression_builder.register(ComplementedCharacterClassExpressionBuilder)
@_walk_expression_builder.register(DoubleQuotedLiteralExpressionBuilder)
@_walk_expression_builder.register(RuleReferenceBuilder)
@_walk_expression_builder.register(SingleQuotedLiteralExpressionBuilder)
def _(
    expression_builder: (
        AnyCharacterExpressionBuilder
        | CharacterClassExpressionBuilder
        | ComplementedCharacterClassExpressionBuilder
        | DoubleQuotedLiteralExpressionBuilder
        | RuleReferenceBuilder
        | SingleQuotedLiteralExpressionBuilder
    ),
    /,
    *,
    expression_builders: Sequence[ExpressionBuilder[AnyMatch, AnyMismatch]],
    used_expression_builder_indices: list[bool],
) -> None:
    return


@_walk_expression_builder.register(ExactRepetitionExpressionBuilder)
@_walk_expression_builder.register(NegativeLookaheadExpressionBuilder)
@_walk_expression_builder.register(OneOrMoreExpressionBuilder)
@_walk_expression_builder.register(OptionalExpressionBuilder)
@_walk_expression_builder.register(PositiveLookaheadExpressionBuilder)
@_walk_expression_builder.register(PositiveOrMoreExpressionBuilder)
@_walk_expression_builder.register(PositiveRepetitionRangeExpressionBuilder)
@_walk_expression_builder.register(ZeroOrMoreExpressionBuilder)
@_walk_expression_builder.register(ZeroRepetitionRangeExpressionBuilder)
def _(
    expression_builder: (
        ExactRepetitionExpressionBuilder
        | NegativeLookaheadExpressionBuilder
        | OneOrMoreExpressionBuilder
        | OptionalExpressionBuilder
        | PositiveLookaheadExpressionBuilder
        | PositiveOrMoreExpressionBuilder
        | PositiveRepetitionRangeExpressionBuilder
        | ZeroOrMoreExpressionBuilder
        | ZeroRepetitionRangeExpressionBuilder
    ),
    /,
    *,
    expression_builders: Sequence[ExpressionBuilder[AnyMatch, AnyMismatch]],
    used_expression_builder_indices: list[bool],
) -> None:
    expression_builder_index = expression_builder.expression_builder_index
    used_expression_builder_indices[expression_builder_index] = True
    _walk_expression_builder(
        expression_builders[expression_builder_index],
        expression_builders=expression_builders,
        used_expression_builder_indices=used_expression_builder_indices,
    )


@_walk_expression_builder.register(PrioritizedChoiceExpressionBuilder)
def _(
    expression_builder: PrioritizedChoiceExpressionBuilder,
    /,
    *,
    expression_builders: Sequence[ExpressionBuilder[AnyMatch, AnyMismatch]],
    used_expression_builder_indices: list[bool],
) -> None:
    variant_builder_indices = expression_builder.variant_builder_indices
    for variant_builder_index in variant_builder_indices:
        used_expression_builder_indices[variant_builder_index] = True
    for variant_builder_index in variant_builder_indices:
        _walk_expression_builder(
            expression_builders[variant_builder_index],
            expression_builders=expression_builders,
            used_expression_builder_indices=used_expression_builder_indices,
        )


@_walk_expression_builder.register(SequenceExpressionBuilder)
def _(
    expression_builder: SequenceExpressionBuilder,
    /,
    *,
    expression_builders: Sequence[ExpressionBuilder[AnyMatch, AnyMismatch]],
    used_expression_builder_indices: list[bool],
) -> None:
    element_builder_indices = expression_builder.element_builder_indices
    for element_builder_index in element_builder_indices:
        used_expression_builder_indices[element_builder_index] = True
    for element_builder_index in element_builder_indices:
        _walk_expression_builder(
            expression_builders[element_builder_index],
            expression_builders=expression_builders,
            used_expression_builder_indices=used_expression_builder_indices,
        )
