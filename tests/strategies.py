import string
from _operator import add
from collections.abc import Callable, Mapping, Sequence
from enum import IntEnum, auto
from functools import partial, wraps
from operator import itemgetter
from typing import Any, Final, TypeVar

from hypothesis import strategies as st
from typing_extensions import Unpack

from pagen.models import (
    CharacterRange,
    CharacterSet,
    ExactRepetitionExpression,
    GrammarBuilder,
    PositiveOrMoreExpression,
    PositiveRepetitionRangeExpression,
    ZeroRepetitionRangeExpression,
)

MAX_EXPRESSION_BUILDER_ELEMENTS_COUNT: Final[int] = 8
MAX_REPETITION_RANGE_BOUND: Final[int] = 16


class ExpressionCategory(IntEnum):
    MAYBE_NON_PROGRESSING = auto()
    PROGRESSING = auto()


CategorizedRuleNames = Mapping[ExpressionCategory, Sequence[str]]
ExpressionRegistrator = Callable[[GrammarBuilder, CategorizedRuleNames], int]


_T = TypeVar('_T')


def partial_right(
    function: Callable[..., _T], *tail_args: Any, **tail_kwargs: Any
) -> Callable[..., _T]:
    @wraps(function)
    def wrapped(*head_args: Any, **head_kwargs: Any) -> _T:
        return function(*head_args, *tail_args, **head_kwargs, **tail_kwargs)

    return wrapped


def to_grammar_builder_strategy(
    *, with_lookahead: bool
) -> st.SearchStrategy[GrammarBuilder]:
    def build_builders(
        categorized_rule_expression_registrators: Mapping[
            str, tuple[ExpressionCategory, ExpressionRegistrator]
        ],
        /,
    ) -> GrammarBuilder:
        result = GrammarBuilder()
        rule_names: dict[ExpressionCategory, list[str]] = {
            expression_category: []
            for expression_category in ExpressionCategory
        }
        for rule_name, (
            expression_category,
            _,
        ) in categorized_rule_expression_registrators.items():
            rule_names[expression_category].append(rule_name)
        for rule_name, (
            _,
            expression_registrator,
        ) in categorized_rule_expression_registrators.items():
            result.add_rule(
                rule_name, expression_registrator(result, rule_names)
            )
        return result

    def to_maybe_non_progressing_expression_registrators(
        progressing_expression_registrator_strategy: st.SearchStrategy[
            ExpressionRegistrator
        ],
        /,
    ) -> st.SearchStrategy[ExpressionRegistrator]:
        def register_optional_expression(
            grammar_builder: GrammarBuilder,
            categorized_rule_names: CategorizedRuleNames,
            expression_registrator: ExpressionRegistrator,
            /,
        ) -> int:
            return grammar_builder.optional_expression(
                expression_registrator(grammar_builder, categorized_rule_names)
            )

        def register_zero_or_more_expression(
            grammar_builder: GrammarBuilder,
            categorized_rule_names: CategorizedRuleNames,
            expression_registrator: ExpressionRegistrator,
            /,
        ) -> int:
            return grammar_builder.zero_or_more_expression(
                expression_registrator(grammar_builder, categorized_rule_names)
            )

        def register_zero_repetition_range_expression(
            grammar_builder: GrammarBuilder,
            categorized_rule_names: CategorizedRuleNames,
            expression_registrator: ExpressionRegistrator,
            end: int,
            /,
        ) -> int:
            return grammar_builder.zero_repetition_range_expression(
                expression_registrator(
                    grammar_builder, categorized_rule_names
                ),
                end,
            )

        variants: list[st.SearchStrategy[ExpressionRegistrator]] = [
            st.builds(
                partial(
                    partial_right,
                    register_rule_reference,
                    expression_category=(
                        ExpressionCategory.MAYBE_NON_PROGRESSING
                    ),
                ),
                st.integers(0),
            ),
            progressing_expression_registrator_strategy.map(
                partial(partial_right, register_optional_expression)
            ),
            progressing_expression_registrator_strategy.map(
                partial(partial_right, register_zero_or_more_expression)
            ),
            st.builds(
                partial(
                    partial_right, register_zero_repetition_range_expression
                ),
                progressing_expression_registrator_strategy,
                st.integers(
                    ZeroRepetitionRangeExpression.MIN_END,
                    MAX_REPETITION_RANGE_BOUND,
                ),
            ),
        ]
        if with_lookahead:

            def register_negative_lookahead_expression(
                grammar_builder: GrammarBuilder,
                categorized_rule_names: CategorizedRuleNames,
                expression_registrator: ExpressionRegistrator,
                /,
            ) -> int:
                return grammar_builder.negative_lookahead_expression(
                    expression_registrator(
                        grammar_builder, categorized_rule_names
                    )
                )

            def register_positive_lookahead_expression(
                grammar_builder: GrammarBuilder,
                categorized_rule_names: CategorizedRuleNames,
                expression_registrator: ExpressionRegistrator,
                /,
            ) -> int:
                return grammar_builder.positive_lookahead_expression(
                    expression_registrator(
                        grammar_builder, categorized_rule_names
                    )
                )

            variants.extend(
                [
                    progressing_expression_registrator_strategy.map(
                        partial(
                            partial_right,
                            register_negative_lookahead_expression,
                        )
                    ),
                    progressing_expression_registrator_strategy.map(
                        partial(
                            partial_right,
                            register_positive_lookahead_expression,
                        )
                    ),
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

    def extend_progressing_expression_registrators(
        step_strategy: st.SearchStrategy[ExpressionRegistrator], /
    ) -> st.SearchStrategy[ExpressionRegistrator]:
        def register_wrapping_expression(
            grammar_builder: GrammarBuilder,
            categorized_rule_names: CategorizedRuleNames,
            result_expression_registrator: Callable[
                [GrammarBuilder, int, Unpack[tuple[Any, ...]]], int
            ],
            wrapped_expression_registrator: ExpressionRegistrator,
            /,
            *args: Any,
        ) -> int:
            return result_expression_registrator(
                grammar_builder,
                wrapped_expression_registrator(
                    grammar_builder, categorized_rule_names
                ),
                *args,
            )

        def register_prioritized_choice_expression(
            grammar_builder: GrammarBuilder,
            categorized_rule_names: CategorizedRuleNames,
            variant_registrators: Sequence[ExpressionRegistrator],
            /,
        ) -> int:
            return grammar_builder.prioritized_choice_expression(
                [
                    variant_registrator(
                        grammar_builder, categorized_rule_names
                    )
                    for variant_registrator in variant_registrators
                ]
            )

        def register_sequence_expression(
            grammar_builder: GrammarBuilder,
            categorized_rule_names: CategorizedRuleNames,
            element_registrators: Sequence[ExpressionRegistrator],
            /,
        ) -> int:
            return grammar_builder.sequence_expression(
                [
                    element_registrator(
                        grammar_builder, categorized_rule_names
                    )
                    for element_registrator in element_registrators
                ]
            )

        def insert_by_offset(
            sequence: Sequence[_T], value: _T, offset: int, /
        ) -> Sequence[_T]:
            index = offset % len(sequence)
            return [*sequence[:index], value, *sequence[index:]]

        return st.one_of(
            st.builds(
                partial(
                    partial_right,
                    register_wrapping_expression,
                    GrammarBuilder.exact_repetition_expression,
                ),
                step_strategy,
                st.integers(
                    ExactRepetitionExpression.MIN_COUNT,
                    MAX_REPETITION_RANGE_BOUND,
                ),
            ),
            step_strategy.map(
                partial(
                    partial_right,
                    register_wrapping_expression,
                    GrammarBuilder.one_or_more_expression,
                )
            ),
            st.builds(
                partial(
                    partial_right,
                    register_wrapping_expression,
                    GrammarBuilder.positive_or_more_expression,
                ),
                step_strategy,
                st.integers(
                    PositiveOrMoreExpression.MIN_START,
                    MAX_REPETITION_RANGE_BOUND,
                ),
            ),
            st.builds(
                partial(
                    partial_right,
                    register_wrapping_expression,
                    GrammarBuilder.positive_repetition_range_expression,
                ),
                step_strategy,
                shared_positive_repetition_range_start_strategy,
                st.builds(
                    add,
                    shared_positive_repetition_range_start_strategy,
                    st.integers(1, MAX_REPETITION_RANGE_BOUND // 2),
                ),
            ),
            st.lists(
                step_strategy,
                min_size=2,
                max_size=MAX_EXPRESSION_BUILDER_ELEMENTS_COUNT,
            ).map(
                partial(partial_right, register_prioritized_choice_expression)
            ),
            st.builds(
                insert_by_offset,
                (
                    st.lists(
                        step_strategy.map(
                            lambda expression_registrator: (
                                ExpressionCategory.PROGRESSING,
                                expression_registrator,
                            )
                        )
                        | to_maybe_non_progressing_expression_registrators(
                            step_strategy
                        ).map(
                            lambda expression_registrator: (
                                ExpressionCategory.MAYBE_NON_PROGRESSING,
                                expression_registrator,
                            )
                        ),
                        min_size=1,
                        max_size=MAX_EXPRESSION_BUILDER_ELEMENTS_COUNT,
                    )
                    .filter(
                        lambda categorized_expression_registrators: any(
                            (
                                expression_category
                                is ExpressionCategory.PROGRESSING
                            )
                            for expression_category, _ in (
                                categorized_expression_registrators
                            )
                        )
                    )
                    .map(partial(map, itemgetter(1)))
                    .map(list)
                ),
                step_strategy,
                st.integers(0),
            ).map(partial(partial_right, register_sequence_expression)),
        )

    character_range_strategy = st.lists(
        st.characters(), min_size=2, max_size=2, unique=True
    ).map(lambda character_pair: CharacterRange(*sorted(character_pair)))
    character_set_strategy = st.builds(CharacterSet, st.text(min_size=1))

    def register_rule_reference(
        grammar_builder: GrammarBuilder,
        categorized_rule_names: CategorizedRuleNames,
        offset: int,
        /,
        *,
        expression_category: ExpressionCategory,
    ) -> int:
        category_rule_names = categorized_rule_names[expression_category]
        if len(category_rule_names) == 0:
            assert (
                expression_category is ExpressionCategory.MAYBE_NON_PROGRESSING
            )
            category_rule_names = categorized_rule_names[
                ExpressionCategory.PROGRESSING
            ]
        return grammar_builder.rule_reference(
            category_rule_names[offset % len(category_rule_names)]
        )

    def to_skipping_rule_names_expression_registrator(
        function: Callable[[GrammarBuilder], int], /
    ) -> ExpressionRegistrator:
        @wraps(function)
        def wrapped(
            grammar_builder: GrammarBuilder,
            categorized_rule_names: CategorizedRuleNames,
            /,
        ) -> int:
            return function(grammar_builder)

        return wrapped

    plain_progressing_expression_registrators: st.SearchStrategy[
        ExpressionRegistrator
    ] = st.recursive(
        st.one_of(
            [
                st.just(
                    to_skipping_rule_names_expression_registrator(
                        GrammarBuilder.any_character_expression
                    )
                ),
                st.builds(
                    partial(
                        partial_right,
                        partial(
                            register_rule_reference,
                            expression_category=ExpressionCategory.PROGRESSING,
                        ),
                    ),
                    st.integers(0),
                ),
                string_literal_value_strategy.map(
                    partial(
                        partial_right,
                        GrammarBuilder.double_quoted_literal_expression,
                    )
                ).map(to_skipping_rule_names_expression_registrator),
                string_literal_value_strategy.map(
                    partial(
                        partial_right,
                        GrammarBuilder.single_quoted_literal_expression,
                    )
                ).map(to_skipping_rule_names_expression_registrator),
                st.builds(
                    partial(
                        partial_right,
                        GrammarBuilder.character_class_expression,
                    ),
                    st.lists(
                        character_range_strategy | character_set_strategy,
                        min_size=1,
                        max_size=MAX_EXPRESSION_BUILDER_ELEMENTS_COUNT,
                    ),
                ).map(to_skipping_rule_names_expression_registrator),
                st.builds(
                    partial(
                        partial_right,
                        GrammarBuilder.complemented_character_class_expression,
                    ),
                    st.lists(
                        character_range_strategy | character_set_strategy,
                        min_size=1,
                        max_size=MAX_EXPRESSION_BUILDER_ELEMENTS_COUNT,
                    ),
                ).map(to_skipping_rule_names_expression_registrator),
            ]
        ),
        extend_progressing_expression_registrators,
        max_leaves=3,
    )
    return (
        st.dictionaries(
            rule_name_strategy,
            (
                plain_progressing_expression_registrators.map(
                    lambda expression_registrator: (
                        ExpressionCategory.PROGRESSING,
                        expression_registrator,
                    )
                )
                | to_maybe_non_progressing_expression_registrators(
                    plain_progressing_expression_registrators
                ).map(
                    lambda expression_registrator: (
                        ExpressionCategory.MAYBE_NON_PROGRESSING,
                        expression_registrator,
                    )
                )
            ),
            min_size=1,
        )
        .filter(
            lambda rule_expression_registrators: any(
                expression_category is ExpressionCategory.PROGRESSING
                for expression_category, _ in (
                    rule_expression_registrators.values()
                )
            )
        )
        .map(build_builders)
    )


identifier_start_characters = '_' + string.ascii_letters
rule_name_strategy: st.SearchStrategy[str] = st.builds(
    add,
    st.text(st.sampled_from(identifier_start_characters), min_size=1),
    st.text(st.sampled_from(identifier_start_characters + string.digits)),
)
string_literal_value_strategy = st.text(min_size=1)
grammar_builder_strategy = to_grammar_builder_strategy(with_lookahead=False)


def is_valid_grammar_builder(value: GrammarBuilder, /) -> bool:
    try:
        value.build()
    except ValueError:
        return False
    else:
        return True


grammar_strategy = grammar_builder_strategy.filter(
    is_valid_grammar_builder
).map(GrammarBuilder.build)
