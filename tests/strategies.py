import string
from _operator import add
from collections.abc import Callable, Mapping, Sequence
from enum import IntEnum, auto
from functools import partial
from typing import Any, Final, Literal, TypeAlias

from hypothesis import strategies as st

from pagen.models import (
    AnyCharacterExpressionBuilder,
    CharacterClassExpressionBuilder,
    CharacterRange,
    CharacterSet,
    ComplementedCharacterClassExpressionBuilder,
    DoubleQuotedLiteralExpressionBuilder,
    ExactRepetitionExpression,
    ExactRepetitionExpressionBuilder,
    ExpressionBuilder,
    GrammarBuilder,
    MatchLeaf,
    MatchTree,
    MismatchLeaf,
    MismatchTree,
    NegativeLookaheadExpressionBuilder,
    OneOrMoreExpressionBuilder,
    OptionalExpressionBuilder,
    PositiveLookaheadExpressionBuilder,
    PositiveOrMoreExpression,
    PositiveOrMoreExpressionBuilder,
    PositiveRepetitionRangeExpression,
    PositiveRepetitionRangeExpressionBuilder,
    PrioritizedChoiceExpressionBuilder,
    RuleReferenceBuilder,
    SequenceExpressionBuilder,
    SingleQuotedLiteralExpressionBuilder,
    ZeroOrMoreExpressionBuilder,
    ZeroRepetitionRangeExpression,
    ZeroRepetitionRangeExpressionBuilder,
)

MAX_EXPRESSION_BUILDER_ELEMENTS_COUNT: Final[int] = 8
MAX_REPETITION_RANGE_BOUND: Final[int] = 16


class ExpressionBuilderCategory(IntEnum):
    MAYBE_NON_PROGRESSING = auto()
    PROGRESSING = auto()


ExpressionBuilderFactory: TypeAlias = Callable[
    [
        Mapping[str, ExpressionBuilder[Any, Any]],
        Mapping[ExpressionBuilderCategory, Sequence[str]],
    ],
    ExpressionBuilder[Any, Any],
]
MaybeNonProgressingExpressionBuilder: TypeAlias = (
    NegativeLookaheadExpressionBuilder
    | OptionalExpressionBuilder
    | PositiveLookaheadExpressionBuilder
    | ZeroOrMoreExpressionBuilder
    | ZeroRepetitionRangeExpressionBuilder
)
ProgressingExpressionBuilder: TypeAlias = (
    ExactRepetitionExpressionBuilder
    | OneOrMoreExpressionBuilder
    | PositiveRepetitionRangeExpressionBuilder
    | PositiveOrMoreExpressionBuilder
)


def to_expression_builders_strategy(
    *, with_lookahead: bool
) -> st.SearchStrategy[Mapping[str, ExpressionBuilder[Any, Any]]]:
    def to_categorized_prioritized_choice_expression_builder_factory(
        categorized_offsets: Sequence[tuple[ExpressionBuilderCategory, int]], /
    ) -> tuple[ExpressionBuilderCategory, ExpressionBuilderFactory]:
        def expression_builder_factory(
            expression_builders: Mapping[str, ExpressionBuilder[Any, Any]],
            categorized_rule_names: Mapping[
                ExpressionBuilderCategory, Sequence[str]
            ],
            /,
        ) -> PrioritizedChoiceExpressionBuilder:
            return PrioritizedChoiceExpressionBuilder(
                [
                    RuleReferenceBuilder(
                        categorized_rule_names[category][
                            offset % len(categorized_rule_names[category])
                        ],
                        expression_builders=expression_builders,
                    )
                    for category, offset in categorized_offsets
                ]
            )

        return (
            (
                ExpressionBuilderCategory.PROGRESSING
                if all(
                    category is ExpressionBuilderCategory.PROGRESSING
                    for category, _ in categorized_offsets
                )
                else ExpressionBuilderCategory.MAYBE_NON_PROGRESSING
            ),
            expression_builder_factory,
        )

    def to_categorized_progressing_expression_builder(
        categorized_offset: tuple[
            Literal[ExpressionBuilderCategory.PROGRESSING], int
        ],
        /,
        *args: Any,
        expression_builder_cls: type[ProgressingExpressionBuilder],
    ) -> tuple[
        Literal[ExpressionBuilderCategory.PROGRESSING],
        ExpressionBuilderFactory,
    ]:
        category, offset = categorized_offset
        assert category is ExpressionBuilderCategory.PROGRESSING, category

        def expression_builder_factory(
            expression_builders: Mapping[str, ExpressionBuilder[Any, Any]],
            categorized_rule_names: Mapping[
                ExpressionBuilderCategory, Sequence[str]
            ],
            /,
        ) -> ExpressionBuilder[Any, Any]:
            return expression_builder_cls(
                RuleReferenceBuilder(
                    categorized_rule_names[category][
                        offset % len(categorized_rule_names[category])
                    ],
                    expression_builders=expression_builders,
                ),
                *args,
            )

        return (
            ExpressionBuilderCategory.PROGRESSING,
            expression_builder_factory,
        )

    def to_categorized_sequence_expression_builder_factory(
        categorized_offsets: Sequence[tuple[ExpressionBuilderCategory, int]], /
    ) -> tuple[
        Literal[ExpressionBuilderCategory.PROGRESSING],
        ExpressionBuilderFactory,
    ]:
        def expression_builder_factory(
            expression_builders: Mapping[str, ExpressionBuilder[Any, Any]],
            categorized_rule_names: Mapping[
                ExpressionBuilderCategory, Sequence[str]
            ],
            /,
        ) -> SequenceExpressionBuilder:
            return SequenceExpressionBuilder(
                [
                    RuleReferenceBuilder(
                        categorized_rule_names[category][
                            offset % len(categorized_rule_names[category])
                        ],
                        expression_builders=expression_builders,
                    )
                    for category, offset in categorized_offsets
                ]
            )

        return (
            ExpressionBuilderCategory.PROGRESSING,
            expression_builder_factory,
        )

    def to_categorized_lookahead_expression_builder(
        categorized_offset: tuple[
            Literal[ExpressionBuilderCategory.PROGRESSING], int
        ],
        /,
        *args: Any,
        expression_builder_cls: type[MaybeNonProgressingExpressionBuilder],
    ) -> tuple[
        Literal[ExpressionBuilderCategory.MAYBE_NON_PROGRESSING],
        ExpressionBuilderFactory,
    ]:
        category, offset = categorized_offset
        assert category is ExpressionBuilderCategory.PROGRESSING, category

        def expression_builder_factory(
            expression_builders: Mapping[str, ExpressionBuilder[Any, Any]],
            categorized_rule_names: Mapping[
                ExpressionBuilderCategory, Sequence[str]
            ],
            /,
        ) -> ExpressionBuilder[Any, Any]:
            return expression_builder_cls(
                RuleReferenceBuilder(
                    categorized_rule_names[category][
                        offset % len(categorized_rule_names[category])
                    ],
                    expression_builders=expression_builders,
                ),
                *args,
            )

        return (
            ExpressionBuilderCategory.MAYBE_NON_PROGRESSING,
            expression_builder_factory,
        )

    def build_builders(
        categorized_expression_builder_factories: Mapping[
            str, tuple[ExpressionBuilderCategory, ExpressionBuilderFactory]
        ],
        /,
    ) -> Mapping[str, ExpressionBuilder[Any, Any]]:
        result: dict[str, ExpressionBuilder[Any, Any]] = {}
        categorized_rule_names: dict[ExpressionBuilderCategory, list[str]] = {}
        for rule_name, (
            expression_builder_category,
            _,
        ) in categorized_expression_builder_factories.items():
            categorized_rule_names.setdefault(
                expression_builder_category, []
            ).append(rule_name)
            if (
                expression_builder_category
                is ExpressionBuilderCategory.PROGRESSING
            ):
                categorized_rule_names.setdefault(
                    ExpressionBuilderCategory.MAYBE_NON_PROGRESSING, []
                ).append(rule_name)
        for rule_name, (
            _,
            expression_builder_factory,
        ) in categorized_expression_builder_factories.items():
            result[rule_name] = expression_builder_factory(
                result, categorized_rule_names
            )
        return result

    progressing_offset_strategy: st.SearchStrategy[
        tuple[Literal[ExpressionBuilderCategory.PROGRESSING], int]
    ] = st.tuples(
        st.just(ExpressionBuilderCategory.PROGRESSING), st.integers(0)
    )
    any_category_offset_strategy = st.tuples(
        st.sampled_from(tuple(ExpressionBuilderCategory)), st.integers(0)
    )

    def to_maybe_non_progressing_expression_builders(
        base: st.SearchStrategy[
            ExpressionBuilder[
                MatchLeaf | MatchTree, MismatchLeaf | MismatchTree
            ]
        ],
        /,
    ) -> st.SearchStrategy[MaybeNonProgressingExpressionBuilder]:
        variants: list[
            st.SearchStrategy[MaybeNonProgressingExpressionBuilder]
        ] = [
            base.map(OptionalExpressionBuilder),
            base.map(ZeroOrMoreExpressionBuilder),
            st.builds(
                ZeroRepetitionRangeExpressionBuilder,
                base,
                st.integers(
                    ZeroRepetitionRangeExpression.MIN_END,
                    MAX_REPETITION_RANGE_BOUND,
                ),
            ),
        ]
        if with_lookahead:
            variants.extend(
                [
                    base.map(NegativeLookaheadExpressionBuilder),
                    base.map(PositiveLookaheadExpressionBuilder),
                ]
            )
        return st.one_of(variants)

    shared_positive_repetition_range_start_strategy = st.shared(
        st.integers(
            PositiveRepetitionRangeExpression.MIN_START,
            MAX_REPETITION_RANGE_BOUND // 2,
        ),
        key='start',
    )

    def extend_progressing_non_recursive_expression_builders(
        step: st.SearchStrategy[
            ExpressionBuilder[
                MatchLeaf | MatchTree, MismatchLeaf | MismatchTree
            ]
        ],
        /,
    ) -> st.SearchStrategy[
        ExpressionBuilder[MatchLeaf | MatchTree, MismatchLeaf | MismatchTree]
    ]:
        prioritized_choice_expression_builder_strategy: st.SearchStrategy[
            PrioritizedChoiceExpressionBuilder[Any]
        ] = st.lists(
            step, min_size=2, max_size=MAX_EXPRESSION_BUILDER_ELEMENTS_COUNT
        ).map(PrioritizedChoiceExpressionBuilder)
        return st.one_of(
            st.builds(
                ExactRepetitionExpressionBuilder,
                step,
                st.integers(
                    ExactRepetitionExpression.MIN_COUNT,
                    MAX_REPETITION_RANGE_BOUND,
                ),
            ),
            step.map(OneOrMoreExpressionBuilder),
            st.builds(
                PositiveOrMoreExpressionBuilder,
                step,
                st.integers(
                    PositiveOrMoreExpression.MIN_START,
                    MAX_REPETITION_RANGE_BOUND,
                ),
            ),
            st.builds(
                PositiveRepetitionRangeExpressionBuilder,
                step,
                shared_positive_repetition_range_start_strategy,
                st.builds(
                    add,
                    shared_positive_repetition_range_start_strategy,
                    st.integers(1, MAX_REPETITION_RANGE_BOUND // 2),
                ),
            ),
            prioritized_choice_expression_builder_strategy,
            (
                st.lists(
                    step | to_maybe_non_progressing_expression_builders(step),
                    min_size=2,
                    max_size=MAX_EXPRESSION_BUILDER_ELEMENTS_COUNT,
                )
                .filter(
                    lambda element_builders: any(
                        not isinstance(
                            element_builder,
                            MaybeNonProgressingExpressionBuilder,
                        )
                        for element_builder in element_builders
                    )
                )
                .map(SequenceExpressionBuilder)
            ),
        )

    character_range_strategy = st.lists(
        st.characters(), min_size=2, max_size=2, unique=True
    ).map(lambda character_pair: CharacterRange(*sorted(character_pair)))
    character_set_strategy = st.builds(CharacterSet, st.text(min_size=1))
    non_recursive_progressing_expression_builders = st.recursive(
        st.one_of(
            [
                st.builds(AnyCharacterExpressionBuilder),
                st.builds(
                    DoubleQuotedLiteralExpressionBuilder,
                    string_literal_value_strategy,
                ),
                st.builds(
                    SingleQuotedLiteralExpressionBuilder,
                    string_literal_value_strategy,
                ),
                st.builds(
                    CharacterClassExpressionBuilder,
                    st.lists(
                        character_range_strategy | character_set_strategy,
                        min_size=1,
                        max_size=MAX_EXPRESSION_BUILDER_ELEMENTS_COUNT,
                    ),
                ),
                st.builds(
                    ComplementedCharacterClassExpressionBuilder,
                    st.lists(
                        character_range_strategy | character_set_strategy,
                        min_size=1,
                        max_size=MAX_EXPRESSION_BUILDER_ELEMENTS_COUNT,
                    ),
                ),
            ]
        ),
        extend_progressing_non_recursive_expression_builders,
        max_leaves=3,
    )
    return (
        st.dictionaries(
            rule_name_strategy,
            st.one_of(
                [
                    non_recursive_progressing_expression_builders.map(
                        lambda builder: (
                            ExpressionBuilderCategory.PROGRESSING,
                            lambda expression_builders, rule_names, /: builder,
                        )
                    ),
                    to_maybe_non_progressing_expression_builders(
                        non_recursive_progressing_expression_builders
                    ).map(
                        lambda builder: (
                            ExpressionBuilderCategory.MAYBE_NON_PROGRESSING,
                            lambda expression_builders, rule_names, /: builder,
                        )
                    ),
                    st.builds(
                        partial(
                            to_categorized_progressing_expression_builder,
                            expression_builder_cls=(
                                ExactRepetitionExpressionBuilder
                            ),
                        ),
                        progressing_offset_strategy,
                        st.integers(
                            ExactRepetitionExpression.MIN_COUNT,
                            MAX_REPETITION_RANGE_BOUND,
                        ),
                    ),
                    progressing_offset_strategy.map(
                        partial(
                            to_categorized_progressing_expression_builder,
                            expression_builder_cls=OneOrMoreExpressionBuilder,
                        )
                    ),
                    st.builds(
                        partial(
                            to_categorized_progressing_expression_builder,
                            expression_builder_cls=(
                                PositiveOrMoreExpressionBuilder
                            ),
                        ),
                        progressing_offset_strategy,
                        st.integers(
                            PositiveOrMoreExpression.MIN_START,
                            MAX_REPETITION_RANGE_BOUND,
                        ),
                    ),
                    st.builds(
                        partial(
                            to_categorized_progressing_expression_builder,
                            expression_builder_cls=(
                                PositiveRepetitionRangeExpressionBuilder
                            ),
                        ),
                        progressing_offset_strategy,
                        shared_positive_repetition_range_start_strategy,
                        st.builds(
                            add,
                            shared_positive_repetition_range_start_strategy,
                            st.integers(1, MAX_REPETITION_RANGE_BOUND // 2),
                        ),
                    ),
                    progressing_offset_strategy.map(
                        partial(
                            to_categorized_lookahead_expression_builder,
                            expression_builder_cls=OptionalExpressionBuilder,
                        )
                    ),
                    progressing_offset_strategy.map(
                        partial(
                            to_categorized_lookahead_expression_builder,
                            expression_builder_cls=ZeroOrMoreExpressionBuilder,
                        )
                    ),
                    st.builds(
                        partial(
                            to_categorized_lookahead_expression_builder,
                            expression_builder_cls=(
                                ZeroRepetitionRangeExpressionBuilder
                            ),
                        ),
                        progressing_offset_strategy,
                        st.integers(
                            ZeroRepetitionRangeExpression.MIN_END,
                            MAX_REPETITION_RANGE_BOUND,
                        ),
                    ),
                    st.lists(
                        any_category_offset_strategy,
                        min_size=2,
                        max_size=MAX_EXPRESSION_BUILDER_ELEMENTS_COUNT,
                    ).map(
                        to_categorized_prioritized_choice_expression_builder_factory
                    ),
                    (
                        st.lists(
                            any_category_offset_strategy,
                            min_size=2,
                            max_size=MAX_EXPRESSION_BUILDER_ELEMENTS_COUNT,
                        )
                        .filter(
                            lambda categorized_offsets: any(
                                (
                                    category
                                    is ExpressionBuilderCategory.PROGRESSING
                                )
                                for category, _ in categorized_offsets
                            )
                        )
                        .map(
                            to_categorized_sequence_expression_builder_factory
                        )
                    ),
                ]
                + (
                    [
                        progressing_offset_strategy.map(
                            partial(
                                to_categorized_lookahead_expression_builder,
                                expression_builder_cls=(
                                    NegativeLookaheadExpressionBuilder
                                ),
                            )
                        ),
                        progressing_offset_strategy.map(
                            partial(
                                to_categorized_lookahead_expression_builder,
                                expression_builder_cls=(
                                    PositiveLookaheadExpressionBuilder
                                ),
                            )
                        ),
                    ]
                    if with_lookahead
                    else []
                )
            ),
            min_size=1,
        )
        .filter(
            lambda categorized_expression_builder_factories: any(
                category is ExpressionBuilderCategory.PROGRESSING
                for category, _ in (
                    categorized_expression_builder_factories.values()
                )
            )
        )
        .map(build_builders)
    )


identifier_start_characters = '_' + string.ascii_letters
rule_name_strategy = st.builds(
    add,
    st.text(st.sampled_from(identifier_start_characters), min_size=1),
    st.text(st.sampled_from(identifier_start_characters + string.digits)),
)
string_literal_value_strategy = st.text(min_size=1)
grammar_builder_strategy = st.builds(
    GrammarBuilder, to_expression_builders_strategy(with_lookahead=True)
)
grammar_strategy = grammar_builder_strategy.map(GrammarBuilder.build)
