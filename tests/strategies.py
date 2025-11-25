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
    LookaheadMatch,
    MatchLeaf,
    MatchTree,
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


class ExpressionBuilderCategory(IntEnum):
    LOOKAHEAD = auto()
    PROGRESSING = auto()


ExpressionBuilderFactory: TypeAlias = Callable[
    [
        Mapping[str, ExpressionBuilder[Any]],
        Mapping[ExpressionBuilderCategory, Sequence[str]],
    ],
    ExpressionBuilder[Any],
]
LookaheadExpressionBuilder: TypeAlias = (
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
LOOKAHEAD_EXPRESSION_BUILDER_CLASSES: Final[
    Sequence[type[LookaheadExpressionBuilder]]
] = [
    NegativeLookaheadExpressionBuilder,
    OptionalExpressionBuilder,
    PositiveLookaheadExpressionBuilder,
    ZeroOrMoreExpressionBuilder,
]


def to_expression_builders_strategy() -> st.SearchStrategy[
    Mapping[str, ExpressionBuilder[Any]]
]:
    def to_categorized_prioritized_choice_expression_builder_factory(
        categorized_offsets: Sequence[tuple[ExpressionBuilderCategory, int]], /
    ) -> tuple[ExpressionBuilderCategory, ExpressionBuilderFactory]:
        def expression_builder_factory(
            expression_builders: Mapping[str, ExpressionBuilder[Any]],
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
                else ExpressionBuilderCategory.LOOKAHEAD
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
            expression_builders: Mapping[str, ExpressionBuilder[Any]],
            categorized_rule_names: Mapping[
                ExpressionBuilderCategory, Sequence[str]
            ],
            /,
        ) -> ExpressionBuilder[Any]:
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
            expression_builders: Mapping[str, ExpressionBuilder[Any]],
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
        expression_builder_cls: type[LookaheadExpressionBuilder],
    ) -> tuple[
        Literal[ExpressionBuilderCategory.LOOKAHEAD], ExpressionBuilderFactory
    ]:
        category, offset = categorized_offset
        assert category is ExpressionBuilderCategory.PROGRESSING, category

        def expression_builder_factory(
            expression_builders: Mapping[str, ExpressionBuilder[Any]],
            categorized_rule_names: Mapping[
                ExpressionBuilderCategory, Sequence[str]
            ],
            /,
        ) -> ExpressionBuilder[Any]:
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
            ExpressionBuilderCategory.LOOKAHEAD,
            expression_builder_factory,
        )

    def build_builders(
        categorized_expression_builder_factories: Mapping[
            str, tuple[ExpressionBuilderCategory, ExpressionBuilderFactory]
        ],
        /,
    ) -> Mapping[str, ExpressionBuilder[Any]]:
        result: dict[str, ExpressionBuilder[Any]] = {}
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
                    ExpressionBuilderCategory.LOOKAHEAD, []
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

    def to_lookahead_expression_builders(
        base: st.SearchStrategy[ExpressionBuilder[MatchLeaf | MatchTree]], /
    ) -> st.SearchStrategy[
        ExpressionBuilder[LookaheadMatch | MatchLeaf | MatchTree]
    ]:
        return st.one_of(
            [base.map(cls) for cls in LOOKAHEAD_EXPRESSION_BUILDER_CLASSES]
        )

    def extend_progressing_non_recursive_expression_builders(
        step: st.SearchStrategy[ExpressionBuilder[MatchLeaf | MatchTree]], /
    ) -> st.SearchStrategy[ExpressionBuilder[MatchLeaf | MatchTree]]:
        prioritized_choice_expression_builder_strategy: st.SearchStrategy[
            PrioritizedChoiceExpressionBuilder[Any]
        ] = st.lists(
            step, min_size=2, max_size=MAX_EXPRESSION_BUILDER_ELEMENTS_COUNT
        ).map(PrioritizedChoiceExpressionBuilder)
        shared_positive_repetition_range_start_strategy = st.shared(
            st.integers(PositiveRepetitionRangeExpression.MIN_START),
            key='start',
        )
        return st.one_of(
            st.builds(
                ExactRepetitionExpressionBuilder,
                step,
                st.integers(ExactRepetitionExpression.MIN_COUNT),
            ),
            step.map(OneOrMoreExpressionBuilder),
            st.builds(
                PositiveOrMoreExpressionBuilder,
                step,
                st.integers(PositiveOrMoreExpression.MIN_START),
            ),
            st.builds(
                PositiveRepetitionRangeExpressionBuilder,
                step,
                shared_positive_repetition_range_start_strategy,
                st.builds(
                    add,
                    shared_positive_repetition_range_start_strategy,
                    st.integers(1),
                ),
            ),
            prioritized_choice_expression_builder_strategy,
            (
                st.lists(
                    step | to_lookahead_expression_builders(step),
                    min_size=2,
                    max_size=MAX_EXPRESSION_BUILDER_ELEMENTS_COUNT,
                )
                .filter(
                    lambda element_builders: any(
                        not isinstance(
                            element_builder, LookaheadExpressionBuilder
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
    shared_positive_repetition_range_start_strategy = st.shared(
        st.integers(PositiveRepetitionRangeExpression.MIN_START), key='start'
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
                    to_lookahead_expression_builders(
                        non_recursive_progressing_expression_builders
                    ).map(
                        lambda builder: (
                            ExpressionBuilderCategory.LOOKAHEAD,
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
                        st.integers(ExactRepetitionExpression.MIN_COUNT),
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
                        st.integers(PositiveOrMoreExpression.MIN_START),
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
                            st.integers(1),
                        ),
                    ),
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
                            expression_builder_cls=OptionalExpressionBuilder,
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
                        st.integers(ZeroRepetitionRangeExpression.MIN_END),
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
    GrammarBuilder, to_expression_builders_strategy()
)
grammar_strategy = grammar_builder_strategy.map(GrammarBuilder.build)
