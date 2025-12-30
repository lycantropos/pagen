from __future__ import annotations

from collections.abc import Sequence
from functools import singledispatch
from typing import TypeGuard, TypeVar

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
from .rule import LeftRecursiveRuleBuilder, NonLeftRecursiveRuleBuilder


class GrammarBuilder:
    @property
    def rule_names(self, /) -> Sequence[str]:
        return self._rule_names

    def add_rule(
        self, rule_name: str, rule_expression_builder_index: int, /
    ) -> None:
        rule_expression_builder_index_range = range(
            len(self._expression_builders)
        )
        if (
            rule_expression_builder_index
            not in rule_expression_builder_index_range
        ):
            raise ValueError(
                'Expression builder index is out of range: '
                f'{rule_expression_builder_index!r} is not '
                f'in {rule_expression_builder_index_range!r}.'
            )
        if rule_name in self._rule_names:
            rule_index = self._rule_names.index(rule_name)
            if (
                existing_expression_builder_index := (
                    self._rule_expression_builder_indices[rule_index]
                )
            ) is not None:
                existing_expression_builder = self._expression_builders[
                    existing_expression_builder_index
                ]
                expression_builder = self._expression_builders[
                    rule_expression_builder_index
                ]
                raise ValueError(
                    f'Rule redefinition is not allowed, '
                    f'but for {rule_name!r} tried to replace '
                    f'{existing_expression_builder!r} '
                    f'with {expression_builder!r}.'
                )
            self._rule_expression_builder_indices[rule_index] = (
                rule_expression_builder_index
            )
        else:
            assert len(self._rule_names) == len(
                self._rule_expression_builder_indices
            ), self
            self._rule_names.append(rule_name)
            self._rule_expression_builder_indices.append(
                rule_expression_builder_index
            )

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

    def rule_reference(self, rule_name: str, /) -> int:
        if rule_name in self._rule_names:
            rule_index = self._rule_names.index(rule_name)
        else:
            rule_index = len(self._rule_names)
            assert len(self._rule_names) == len(
                self._rule_expression_builder_indices
            ), self
            self._rule_names.append(rule_name)
            self._rule_expression_builder_indices.append(None)
        return self._register_expression_builder(
            RuleReferenceBuilder(rule_name, rule_index)
        )

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
    _rule_names: list[str]
    _rule_expression_builder_indices: list[int | None]

    def _build(self, /) -> Grammar:
        rule_expression_builder_indices = (
            self._get_validated_rule_expression_builder_indices()
        )
        return Grammar(
            self._rule_names,
            [
                (
                    LeftRecursiveRuleBuilder
                    if (
                        rule_expression_builder := self._expression_builders[
                            rule_expression_builder_index
                        ]
                    ).is_left_recursive(
                        expression_builders=self._expression_builders,
                        rule_expression_builder_indices=(
                            rule_expression_builder_indices
                        ),
                        visited_rule_indices=set(),
                    )
                    else NonLeftRecursiveRuleBuilder
                )(
                    self._rule_names[rule_index],
                    rule_expression_builder.build(
                        expression_builders=self._expression_builders,
                        rule_expression_builder_indices=(
                            rule_expression_builder_indices
                        ),
                    ),
                )
                for (rule_index, rule_expression_builder_index) in enumerate(
                    rule_expression_builder_indices
                )
            ],
        )

    def _get_validated_rule_expression_builder_indices(
        self, /
    ) -> Sequence[int]:
        result = self._rule_expression_builder_indices
        if not _is_non_none_sequence(result):
            unset_rule_names = [
                self._rule_names[rule_index]
                for rule_index, rule_expression_builder_index in enumerate(
                    result
                )
                if rule_expression_builder_index is None
            ]
            raise ValueError(
                'All rule expression builders should be set, '
                f'but got {unset_rule_names!r}.'
            )
        return result

    def _register_expression_builder(
        self, expression_builder: ExpressionBuilder[AnyMatch, AnyMismatch], /
    ) -> int:
        result = len(self._expression_builders)
        self._expression_builders.append(expression_builder)
        return result

    def _validate(self, /) -> None:
        assert len(self._rule_names) == len(
            self._rule_expression_builder_indices
        ), self
        rule_expression_builder_indices = (
            self._get_validated_rule_expression_builder_indices()
        )
        if (
            len(
                non_terminating_rule_names := [
                    self._rule_names[rule_index]
                    for rule_index, rule_expression_builder_index in enumerate(
                        rule_expression_builder_indices
                    )
                    if not self._expression_builders[
                        rule_expression_builder_index
                    ].is_terminating(
                        expression_builders=self._expression_builders,
                        is_leftmost=True,
                        rule_expression_builder_indices=(
                            rule_expression_builder_indices
                        ),
                        visited_rule_indices=set(),
                    )
                ]
            )
            > 0
        ):
            non_terminating_rule_names.sort()
            raise ValueError(
                'All rules should be terminating, '
                'but the following ones are not: '
                f'{", ".join(map(repr, non_terminating_rule_names))}.'
            )
        used_expression_builder_indices = [False] * len(
            self._expression_builders
        )
        for rule_expression_builder_index in rule_expression_builder_indices:
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

    __slots__ = (
        '_expression_builders',
        '_rule_expression_builder_indices',
        '_rule_names',
    )

    def __init__(
        self,
        expression_builders: (
            list[ExpressionBuilder[AnyMatch, AnyMismatch]] | None
        ) = None,
        rule_names: list[str] | None = None,
        rule_expression_indices: list[int | None] | None = None,
        /,
    ) -> None:
        if not isinstance(expression_builders, list | None):
            raise TypeError(type(expression_builders))
        if not isinstance(rule_expression_indices, dict | None):
            raise TypeError(type(rule_expression_indices))
        self._expression_builders = expression_builders or []
        self._rule_names = rule_names or []
        self._rule_expression_builder_indices = rule_expression_indices or []

    @override
    def __repr__(self, /) -> str:
        return (
            f'{type(self).__qualname__}'
            '('
            f'{self._expression_builders!r}, '
            f'{self._rule_expression_builder_indices!r}'
            ')'
        )


_T = TypeVar('_T')


def _is_non_none_sequence(
    value: Sequence[_T | None], /
) -> TypeGuard[Sequence[_T]]:
    return all(element is not None for element in value)


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
