from __future__ import annotations

import contextlib
import inspect
from collections.abc import Iterator, Mapping
from enum import Enum, unique
from typing import Any, ClassVar, Final, TypeVar, cast

from typing_extensions import override

from . import CharacterRange, CharacterSet
from .constants import (
    CHARACTER_CLASS_SPECIAL_CHARACTERS,
    COMMON_SPECIAL_CHARACTERS,
    DOUBLE_QUOTED_LITERAL_SPECIAL_CHARACTERS,
    SINGLE_QUOTED_LITERAL_SPECIAL_CHARACTERS,
)
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
    SequenceExpressionBuilder,
    SingleQuotedLiteralExpressionBuilder,
    ZeroOrMoreExpressionBuilder,
    ZeroRepetitionRangeExpressionBuilder,
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
from .grammar import Grammar
from .grammar_builder import GrammarBuilder
from .match import AnyMatch, MatchLeaf, MatchTree
from .mismatch import AnyMismatch
from .rule import Rule
from .utils import to_package_non_abstract_subclasses


@unique
class RuleName(str, Enum):
    ANY_CHARACTER = AnyCharacterExpression.__name__
    CHARACTER_CLASS = CharacterClassExpression.__name__
    CHARACTER_CONTAINER = 'CharacterContainer'
    CHARACTER_CONTAINER_ELEMENT = 'CharacterContainerElement'
    CHARACTER_RANGE = CharacterRange.__name__
    CHARACTER_SET = CharacterSet.__name__
    COMPLEMENTED_CHARACTER_CLASS = (
        ComplementedCharacterClassExpression.__name__
    )
    DOUBLE_QUOTED_LITERAL = DoubleQuotedLiteralExpression.__name__
    DOUBLE_QUOTED_LITERAL_CHARACTER = (
        f'{DoubleQuotedLiteralExpression.__name__}Character'
    )
    END_OF_FILE = 'EndOfFile'
    END_OF_LINE = 'EndOfLine'
    EXACT_REPETITION = ExactRepetitionExpression.__name__
    EXPRESSION = Expression.__name__
    FILLER = 'Filler'
    GRAMMAR = Grammar.__name__
    IDENTIFIER = 'Identifier'
    LEFT_ARROW = 'LEFT_ARROW'
    NEGATIVE_LOOKAHEAD = NegativeLookaheadExpression.__name__
    NON_NULLABLE_SEQUENCE_ELEMENT = (
        f'NonNullable{SequenceExpression.__name__}Element'
    )
    NON_NULLABLE_TERM = 'NonNullableTerm'
    NULLABLE_SEQUENCE_ELEMENT = f'Nullable{SequenceExpression.__name__}Element'
    ONE_OR_MORE = OneOrMoreExpression.__name__
    OPTIONAL = OptionalExpression.__name__
    POSITIVE_LOOKAHEAD = PositiveLookaheadExpression.__name__
    POSITIVE_OR_MORE_EXPRESSION = PositiveOrMoreExpression.__name__
    POSITIVE_REPETITION_RANGE = PositiveRepetitionRangeExpression.__name__
    PRIORITIZED_CHOICE = PrioritizedChoiceExpression.__name__
    PRIORITIZED_CHOICE_VARIANT = (
        f'{PrioritizedChoiceExpression.__name__}Variant'
    )
    RULE = Rule.__name__
    RULE_REFERENCE = RuleReference.__name__
    SEQUENCE = SequenceExpression.__name__
    SEQUENCE_ELEMENT = f'{SequenceExpression.__name__}Element'
    SINGLE_LINE_COMMENT = 'SingleLineComment'
    SINGLE_QUOTED_LITERAL = SingleQuotedLiteralExpression.__name__
    SINGLE_QUOTED_LITERAL_CHARACTER = (
        f'{SingleQuotedLiteralExpression.__name__}Character'
    )
    SPACE = 'Space'
    UNSIGNED_INTEGER = 'UnsignedInteger'
    ZERO_OR_MORE = ZeroOrMoreExpression.__name__
    ZERO_REPETITION_RANGE = ZeroRepetitionRangeExpression.__name__

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}.{self._name_}'

    @override
    def __str__(self, /) -> str:
        return self._value_


PARSER_GRAMMAR_BUILDER: Final[GrammarBuilder[Any, Any]] = GrammarBuilder()
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.GRAMMAR,
    SequenceExpressionBuilder(
        [
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
            OneOrMoreExpressionBuilder(
                PARSER_GRAMMAR_BUILDER.get_reference(RuleName.RULE)
            ),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.END_OF_FILE),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.RULE,
    SequenceExpressionBuilder(
        [
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.IDENTIFIER),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.LEFT_ARROW),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.EXPRESSION),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.EXPRESSION,
    PrioritizedChoiceExpressionBuilder(
        [
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.PRIORITIZED_CHOICE),
            PARSER_GRAMMAR_BUILDER.get_reference(
                RuleName.PRIORITIZED_CHOICE_VARIANT
            ),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.PRIORITIZED_CHOICE,
    SequenceExpressionBuilder(
        [
            PARSER_GRAMMAR_BUILDER.get_reference(
                RuleName.PRIORITIZED_CHOICE_VARIANT
            ),
            OneOrMoreExpressionBuilder(
                SequenceExpressionBuilder(
                    [
                        SingleQuotedLiteralExpressionBuilder('/'),
                        PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
                        PARSER_GRAMMAR_BUILDER.get_reference(
                            RuleName.PRIORITIZED_CHOICE_VARIANT
                        ),
                    ]
                )
            ),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.PRIORITIZED_CHOICE_VARIANT,
    PrioritizedChoiceExpressionBuilder(
        [
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.SEQUENCE),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.SEQUENCE_ELEMENT),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.SEQUENCE,
    SequenceExpressionBuilder(
        [
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.SEQUENCE_ELEMENT),
            OneOrMoreExpressionBuilder(
                PARSER_GRAMMAR_BUILDER.get_reference(RuleName.SEQUENCE_ELEMENT)
            ),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.SEQUENCE_ELEMENT,
    PrioritizedChoiceExpressionBuilder(
        [
            PARSER_GRAMMAR_BUILDER.get_reference(
                RuleName.NULLABLE_SEQUENCE_ELEMENT
            ),
            PARSER_GRAMMAR_BUILDER.get_reference(
                RuleName.NON_NULLABLE_SEQUENCE_ELEMENT
            ),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.NON_NULLABLE_SEQUENCE_ELEMENT,
    PrioritizedChoiceExpressionBuilder(
        [
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.EXACT_REPETITION),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.ONE_OR_MORE),
            PARSER_GRAMMAR_BUILDER.get_reference(
                RuleName.POSITIVE_OR_MORE_EXPRESSION
            ),
            PARSER_GRAMMAR_BUILDER.get_reference(
                RuleName.POSITIVE_REPETITION_RANGE
            ),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.NON_NULLABLE_TERM),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.NULLABLE_SEQUENCE_ELEMENT,
    PrioritizedChoiceExpressionBuilder(
        [
            SequenceExpressionBuilder(
                [
                    SingleQuotedLiteralExpressionBuilder('('),
                    PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
                    PARSER_GRAMMAR_BUILDER.get_reference(
                        RuleName.NULLABLE_SEQUENCE_ELEMENT
                    ),
                    SingleQuotedLiteralExpressionBuilder(')'),
                    PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
                ]
            ),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.NEGATIVE_LOOKAHEAD),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.POSITIVE_LOOKAHEAD),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.OPTIONAL),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.ZERO_OR_MORE),
            PARSER_GRAMMAR_BUILDER.get_reference(
                RuleName.ZERO_REPETITION_RANGE
            ),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.NEGATIVE_LOOKAHEAD,
    SequenceExpressionBuilder(
        [
            SingleQuotedLiteralExpressionBuilder('!'),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
            PARSER_GRAMMAR_BUILDER.get_reference(
                RuleName.NON_NULLABLE_SEQUENCE_ELEMENT
            ),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.POSITIVE_LOOKAHEAD,
    SequenceExpressionBuilder(
        [
            SingleQuotedLiteralExpressionBuilder('&'),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
            PARSER_GRAMMAR_BUILDER.get_reference(
                RuleName.NON_NULLABLE_SEQUENCE_ELEMENT
            ),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.EXACT_REPETITION,
    SequenceExpressionBuilder(
        [
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.NON_NULLABLE_TERM),
            SingleQuotedLiteralExpressionBuilder('{'),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.UNSIGNED_INTEGER),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
            SingleQuotedLiteralExpressionBuilder('}'),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.OPTIONAL,
    SequenceExpressionBuilder(
        [
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.NON_NULLABLE_TERM),
            SingleQuotedLiteralExpressionBuilder('?'),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.ONE_OR_MORE,
    SequenceExpressionBuilder(
        [
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.NON_NULLABLE_TERM),
            SingleQuotedLiteralExpressionBuilder('+'),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.POSITIVE_OR_MORE_EXPRESSION,
    SequenceExpressionBuilder(
        [
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.NON_NULLABLE_TERM),
            SingleQuotedLiteralExpressionBuilder('{'),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.UNSIGNED_INTEGER),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
            SingleQuotedLiteralExpressionBuilder(','),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
            SingleQuotedLiteralExpressionBuilder('}'),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.POSITIVE_REPETITION_RANGE,
    SequenceExpressionBuilder(
        [
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.NON_NULLABLE_TERM),
            SingleQuotedLiteralExpressionBuilder('{'),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.UNSIGNED_INTEGER),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
            SingleQuotedLiteralExpressionBuilder(','),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.UNSIGNED_INTEGER),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
            SingleQuotedLiteralExpressionBuilder('}'),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.ZERO_OR_MORE,
    SequenceExpressionBuilder(
        [
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.NON_NULLABLE_TERM),
            SingleQuotedLiteralExpressionBuilder('*'),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.ZERO_REPETITION_RANGE,
    SequenceExpressionBuilder(
        [
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.NON_NULLABLE_TERM),
            SingleQuotedLiteralExpressionBuilder('{'),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
            SingleQuotedLiteralExpressionBuilder(','),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.UNSIGNED_INTEGER),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
            SingleQuotedLiteralExpressionBuilder('}'),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.NON_NULLABLE_TERM,
    PrioritizedChoiceExpressionBuilder(
        [
            SequenceExpressionBuilder(
                [
                    SingleQuotedLiteralExpressionBuilder('('),
                    PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
                    PrioritizedChoiceExpressionBuilder(
                        [
                            PARSER_GRAMMAR_BUILDER.get_reference(
                                RuleName.PRIORITIZED_CHOICE
                            ),
                            PARSER_GRAMMAR_BUILDER.get_reference(
                                RuleName.SEQUENCE
                            ),
                            PARSER_GRAMMAR_BUILDER.get_reference(
                                RuleName.NON_NULLABLE_SEQUENCE_ELEMENT
                            ),
                        ]
                    ),
                    SingleQuotedLiteralExpressionBuilder(')'),
                    PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
                ]
            ),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.ANY_CHARACTER),
            PARSER_GRAMMAR_BUILDER.get_reference(
                RuleName.COMPLEMENTED_CHARACTER_CLASS
            ),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.CHARACTER_CLASS),
            PARSER_GRAMMAR_BUILDER.get_reference(
                RuleName.DOUBLE_QUOTED_LITERAL
            ),
            PARSER_GRAMMAR_BUILDER.get_reference(
                RuleName.SINGLE_QUOTED_LITERAL
            ),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.RULE_REFERENCE),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.RULE_REFERENCE,
    SequenceExpressionBuilder(
        [
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.IDENTIFIER),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
            NegativeLookaheadExpressionBuilder(
                PARSER_GRAMMAR_BUILDER.get_reference(RuleName.LEFT_ARROW)
            ),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.ANY_CHARACTER,
    SequenceExpressionBuilder(
        [
            SingleQuotedLiteralExpressionBuilder('.'),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.DOUBLE_QUOTED_LITERAL_CHARACTER,
    PrioritizedChoiceExpressionBuilder(
        [
            SequenceExpressionBuilder(
                [
                    SingleQuotedLiteralExpressionBuilder('\\'),
                    CharacterClassExpressionBuilder(
                        [
                            CharacterSet(
                                DOUBLE_QUOTED_LITERAL_SPECIAL_CHARACTERS
                                + COMMON_SPECIAL_CHARACTERS
                            )
                        ]
                    ),
                ]
            ),
            SequenceExpressionBuilder(
                [
                    NegativeLookaheadExpressionBuilder(
                        SingleQuotedLiteralExpressionBuilder('\\')
                    ),
                    AnyCharacterExpressionBuilder(),
                ]
            ),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.SINGLE_QUOTED_LITERAL_CHARACTER,
    PrioritizedChoiceExpressionBuilder(
        [
            SequenceExpressionBuilder(
                [
                    SingleQuotedLiteralExpressionBuilder('\\'),
                    CharacterClassExpressionBuilder(
                        [
                            CharacterSet(
                                SINGLE_QUOTED_LITERAL_SPECIAL_CHARACTERS
                                + COMMON_SPECIAL_CHARACTERS
                            )
                        ]
                    ),
                ]
            ),
            SequenceExpressionBuilder(
                [
                    NegativeLookaheadExpressionBuilder(
                        SingleQuotedLiteralExpressionBuilder('\\')
                    ),
                    AnyCharacterExpressionBuilder(),
                ]
            ),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.CHARACTER_CLASS,
    SequenceExpressionBuilder(
        [
            SingleQuotedLiteralExpressionBuilder('['),
            OneOrMoreExpressionBuilder(
                PARSER_GRAMMAR_BUILDER.get_reference(
                    RuleName.CHARACTER_CONTAINER
                )
            ),
            SingleQuotedLiteralExpressionBuilder(']'),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.COMPLEMENTED_CHARACTER_CLASS,
    SequenceExpressionBuilder(
        [
            SingleQuotedLiteralExpressionBuilder('[^'),
            OneOrMoreExpressionBuilder(
                PARSER_GRAMMAR_BUILDER.get_reference(
                    RuleName.CHARACTER_CONTAINER
                )
            ),
            SingleQuotedLiteralExpressionBuilder(']'),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.CHARACTER_CONTAINER,
    PrioritizedChoiceExpressionBuilder(
        [
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.CHARACTER_RANGE),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.CHARACTER_SET),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.CHARACTER_RANGE,
    SequenceExpressionBuilder(
        [
            NegativeLookaheadExpressionBuilder(
                SingleQuotedLiteralExpressionBuilder(']')
            ),
            PARSER_GRAMMAR_BUILDER.get_reference(
                RuleName.CHARACTER_CONTAINER_ELEMENT
            ),
            SingleQuotedLiteralExpressionBuilder('-'),
            PARSER_GRAMMAR_BUILDER.get_reference(
                RuleName.CHARACTER_CONTAINER_ELEMENT
            ),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.CHARACTER_SET,
    OneOrMoreExpressionBuilder(
        SequenceExpressionBuilder(
            [
                NegativeLookaheadExpressionBuilder(
                    SingleQuotedLiteralExpressionBuilder(']')
                ),
                PARSER_GRAMMAR_BUILDER.get_reference(
                    RuleName.CHARACTER_CONTAINER_ELEMENT
                ),
                NegativeLookaheadExpressionBuilder(
                    SingleQuotedLiteralExpressionBuilder('-')
                ),
            ]
        )
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.CHARACTER_CONTAINER_ELEMENT,
    PrioritizedChoiceExpressionBuilder(
        [
            SequenceExpressionBuilder(
                [
                    SingleQuotedLiteralExpressionBuilder('\\'),
                    CharacterClassExpressionBuilder(
                        [
                            CharacterSet(
                                CHARACTER_CLASS_SPECIAL_CHARACTERS
                                + COMMON_SPECIAL_CHARACTERS
                            )
                        ]
                    ),
                ]
            ),
            SequenceExpressionBuilder(
                [
                    NegativeLookaheadExpressionBuilder(
                        SingleQuotedLiteralExpressionBuilder('\\')
                    ),
                    AnyCharacterExpressionBuilder(),
                ]
            ),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.DOUBLE_QUOTED_LITERAL,
    SequenceExpressionBuilder(
        [
            SingleQuotedLiteralExpressionBuilder('"'),
            ZeroOrMoreExpressionBuilder(
                SequenceExpressionBuilder(
                    [
                        NegativeLookaheadExpressionBuilder(
                            SingleQuotedLiteralExpressionBuilder('"')
                        ),
                        PARSER_GRAMMAR_BUILDER.get_reference(
                            RuleName.DOUBLE_QUOTED_LITERAL_CHARACTER
                        ),
                    ]
                )
            ),
            SingleQuotedLiteralExpressionBuilder('"'),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.SINGLE_QUOTED_LITERAL,
    SequenceExpressionBuilder(
        [
            SingleQuotedLiteralExpressionBuilder("'"),
            ZeroOrMoreExpressionBuilder(
                SequenceExpressionBuilder(
                    [
                        NegativeLookaheadExpressionBuilder(
                            SingleQuotedLiteralExpressionBuilder("'")
                        ),
                        PARSER_GRAMMAR_BUILDER.get_reference(
                            RuleName.SINGLE_QUOTED_LITERAL_CHARACTER
                        ),
                    ]
                )
            ),
            SingleQuotedLiteralExpressionBuilder("'"),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.FILLER),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.END_OF_FILE,
    NegativeLookaheadExpressionBuilder(AnyCharacterExpressionBuilder()),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.END_OF_LINE,
    PrioritizedChoiceExpressionBuilder(
        [
            SingleQuotedLiteralExpressionBuilder('\r\n'),
            SingleQuotedLiteralExpressionBuilder('\n'),
            SingleQuotedLiteralExpressionBuilder('\r'),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.IDENTIFIER,
    SequenceExpressionBuilder(
        [
            CharacterClassExpressionBuilder(
                [
                    CharacterRange('a', 'z'),
                    CharacterRange('A', 'Z'),
                    CharacterSet('_'),
                ]
            ),
            ZeroOrMoreExpressionBuilder(
                CharacterClassExpressionBuilder(
                    [
                        CharacterRange('0', '9'),
                        CharacterRange('a', 'z'),
                        CharacterRange('A', 'Z'),
                        CharacterSet('_'),
                    ]
                )
            ),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.FILLER,
    ZeroOrMoreExpressionBuilder(
        PrioritizedChoiceExpressionBuilder(
            [
                PARSER_GRAMMAR_BUILDER.get_reference(RuleName.SPACE),
                PARSER_GRAMMAR_BUILDER.get_reference(
                    RuleName.SINGLE_LINE_COMMENT
                ),
            ]
        )
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.SINGLE_LINE_COMMENT,
    SequenceExpressionBuilder(
        [
            SingleQuotedLiteralExpressionBuilder('#'),
            ZeroOrMoreExpressionBuilder(
                SequenceExpressionBuilder(
                    [
                        NegativeLookaheadExpressionBuilder(
                            PARSER_GRAMMAR_BUILDER.get_reference(
                                RuleName.END_OF_LINE
                            )
                        ),
                        AnyCharacterExpressionBuilder(),
                    ]
                )
            ),
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.END_OF_LINE),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.SPACE,
    PrioritizedChoiceExpressionBuilder(
        [
            PARSER_GRAMMAR_BUILDER.get_reference(RuleName.END_OF_LINE),
            SingleQuotedLiteralExpressionBuilder(' '),
            SingleQuotedLiteralExpressionBuilder('\t'),
        ]
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.UNSIGNED_INTEGER,
    PrioritizedChoiceExpressionBuilder(
        (
            SequenceExpressionBuilder(
                [
                    CharacterClassExpressionBuilder(
                        [CharacterRange('1', '9')]
                    ),
                    ZeroOrMoreExpressionBuilder(
                        CharacterClassExpressionBuilder(
                            [CharacterRange('0', '9')]
                        )
                    ),
                ]
            ),
            cast(
                ExpressionBuilder[MatchLeaf | MatchTree, AnyMismatch],
                SingleQuotedLiteralExpressionBuilder('0'),
            ),
        )
    ),
)
PARSER_GRAMMAR_BUILDER.add_rule(
    RuleName.LEFT_ARROW, SingleQuotedLiteralExpressionBuilder('<-')
)
assert (
    len(
        extra_rule_names := [
            rule_name
            for rule_name in RuleName
            if rule_name not in PARSER_GRAMMAR_BUILDER.expression_builders
        ]
    )
    == 0
), extra_rule_names
assert (
    len(
        missing_expression_classes := [
            cls
            for cls in to_package_non_abstract_subclasses(Expression)  # type: ignore[type-abstract]
            if cls.__name__ not in PARSER_GRAMMAR_BUILDER.expression_builders
        ]
    )
    == 0
), missing_expression_classes
PARSER_GRAMMAR: Final[Grammar[Any, Any]] = PARSER_GRAMMAR_BUILDER.build()
assert (
    len(
        unsupported_classes := [
            cls
            for cls in to_package_non_abstract_subclasses(Expression)  # type: ignore[type-abstract]
            if cls.__name__ not in PARSER_GRAMMAR.rules
        ]
    )
    == 0
), unsupported_classes


def parse_grammar(
    text: str, /, *, parser_grammar: Grammar[Any, Any] = PARSER_GRAMMAR
) -> Grammar[Any, Any]:
    tree = parser_grammar.parse(text, starting_rule_name='Grammar')
    grammar_builder = GrammarBuilder()
    TreeToGrammarVisitor(grammar_builder).visit(tree)
    return grammar_builder.build()


class MatchTreeVisitor:
    VISITOR_METHOD_PREFIX: ClassVar[str] = 'visit_'

    def visit(self, match: AnyMatch, /) -> None:
        (
            self.generic_visit
            if (rule_name := match.rule_name) is None
            else getattr(
                self,
                self.VISITOR_METHOD_PREFIX + rule_name,
                self.generic_visit,
            )
        )(match)

    def generic_visit(self, match: AnyMatch, /) -> None:
        if not isinstance(match, MatchTree):
            return
        for child in match.children:
            self.visit(child)

    def __init_subclass__(cls, /) -> None:
        visitor_signature = inspect.signature(cls.visit, eval_str=True)
        invalid_visitors = [
            (name, signature)
            for name, field in vars(cls).items()
            if (
                name.startswith(cls.VISITOR_METHOD_PREFIX)
                and (
                    (
                        signature := (
                            inspect.signature(field, eval_str=True)
                            if inspect.isfunction(field)
                            else None
                        )
                    )
                    != visitor_signature
                )
            )
        ]
        if len(invalid_visitors) > 0:
            raise ValueError(invalid_visitors)


class TreeToGrammarVisitor(MatchTreeVisitor):
    _COMMON_SPECIAL_CHARACTER_MAPPING: ClassVar[Mapping[str, str]] = {
        ('\\' + character): (
            ('\\' + character).encode('utf-8').decode('unicode-escape')
        )
        for character in COMMON_SPECIAL_CHARACTERS
    }
    _CHARACTER_CLASS_SPECIAL_CHARACTER_MAPPING: ClassVar[Mapping[str, str]] = {
        **{
            '\\' + character: character
            for character in CHARACTER_CLASS_SPECIAL_CHARACTERS
        },
        **_COMMON_SPECIAL_CHARACTER_MAPPING,
    }
    _DOUBLE_QUOTED_LITERAL_SPECIAL_CHARACTER_MAPPING: ClassVar[
        Mapping[str, str]
    ] = {
        **{
            '\\' + character: character
            for character in DOUBLE_QUOTED_LITERAL_SPECIAL_CHARACTERS
        },
        **_COMMON_SPECIAL_CHARACTER_MAPPING,
    }
    _SINGLE_QUOTED_LITERAL_SPECIAL_CHARACTER_MAPPING: ClassVar[
        Mapping[str, str]
    ] = {
        **{
            '\\' + character: character
            for character in SINGLE_QUOTED_LITERAL_SPECIAL_CHARACTERS
        },
        **_COMMON_SPECIAL_CHARACTER_MAPPING,
    }

    def visit_AnyCharacterExpression(  # noqa: N802
        self, match: AnyMatch, /
    ) -> None:
        assert isinstance(match, MatchTree), match
        for child in match.children:
            self.visit(child)
        self._expression_builders[-1].append(AnyCharacterExpressionBuilder())

    def visit_CharacterClassExpression(  # noqa: N802
        self, match: AnyMatch, /
    ) -> None:
        assert isinstance(match, MatchTree), match
        with self._push_character_class_elements() as character_class_elements:
            for child in match.children:
                self.visit(child)
        self._expression_builders[-1].append(
            CharacterClassExpressionBuilder(character_class_elements)
        )

    def visit_CharacterContainerElement(  # noqa: N802
        self, match: AnyMatch, /
    ) -> None:
        assert isinstance(match, MatchLeaf | MatchTree), match
        character = match.characters
        character = self._CHARACTER_CLASS_SPECIAL_CHARACTER_MAPPING.get(
            character, character
        )
        assert len(character) == 1, character
        self._character_class_characters[-1].append(character)

    def visit_CharacterRange(self, match: AnyMatch, /) -> None:  # noqa: N802
        assert isinstance(match, MatchTree), match
        with self._push_character_class_characters() as start_end:
            for child in match.children:
                self.visit(child)
        start, end = start_end
        self._character_class_elements[-1].append(CharacterRange(start, end))

    def visit_CharacterSet(self, match: AnyMatch, /) -> None:  # noqa: N802
        assert isinstance(match, MatchTree), match
        with self._push_character_class_characters() as elements:
            for child in match.children:
                self.visit(child)
        self._character_class_elements[-1].append(
            CharacterSet(''.join(elements))
        )

    def visit_ComplementedCharacterClassExpression(  # noqa: N802
        self, match: AnyMatch, /
    ) -> None:
        assert isinstance(match, MatchTree), match
        with self._push_character_class_elements() as character_class_elements:
            for child in match.children:
                self.visit(child)
        self._expression_builders[-1].append(
            ComplementedCharacterClassExpressionBuilder(
                character_class_elements
            )
        )

    def visit_DoubleQuotedLiteralExpression(  # noqa: N802
        self, match: AnyMatch, /
    ) -> None:
        assert isinstance(match, MatchTree), match
        with self._push_literal_characters() as characters:
            for child in match.children:
                self.visit(child)
        self._expression_builders[-1].append(
            DoubleQuotedLiteralExpressionBuilder(''.join(characters))
        )

    def visit_DoubleQuotedLiteralExpressionCharacter(  # noqa: N802
        self, match: AnyMatch, /
    ) -> None:
        assert isinstance(match, MatchLeaf | MatchTree), match
        character = match.characters
        character = self._DOUBLE_QUOTED_LITERAL_SPECIAL_CHARACTER_MAPPING.get(
            character, character
        )
        assert len(character) == 1, character
        self._literal_characters[-1].append(character)

    def visit_ExactRepetitionExpression(self, match: AnyMatch, /) -> None:
        assert isinstance(match, MatchTree)
        with (
            self._push_expression_builders() as expression_builders,
            self._push_unsigned_integers() as unsigned_integers,
        ):
            for child in match.children:
                self.visit(child)
        (expression_builder,) = expression_builders
        (count,) = unsigned_integers
        self._expression_builders[-1].append(
            ExactRepetitionExpressionBuilder(expression_builder, count)
        )

    def visit_Identifier(self, match: AnyMatch, /) -> None:  # noqa: N802
        assert isinstance(match, MatchLeaf | MatchTree), match
        self._identifiers.append(match.characters)

    def visit_NegativeLookaheadExpression(  # noqa: N802
        self, match: AnyMatch, /
    ) -> None:
        assert isinstance(match, MatchTree), match
        with self._push_expression_builders() as expression_builders:
            for child in match.children:
                self.visit(child)
        (expression_builder,) = expression_builders
        self._expression_builders[-1].append(
            NegativeLookaheadExpressionBuilder(expression_builder)
        )

    def visit_OneOrMoreExpression(  # noqa: N802
        self, match: AnyMatch, /
    ) -> None:
        assert isinstance(match, MatchTree), match
        with self._push_expression_builders() as expression_builders:
            for child in match.children:
                self.visit(child)
        (expression_builder,) = expression_builders
        self._expression_builders[-1].append(
            OneOrMoreExpressionBuilder(expression_builder)
        )

    def visit_PositiveOrMoreExpression(  # noqa: N802
        self, match: AnyMatch, /
    ) -> None:
        assert isinstance(match, MatchTree), match
        with (
            self._push_expression_builders() as expression_builders,
            self._push_unsigned_integers() as unsigned_integers,
        ):
            for child in match.children:
                self.visit(child)
        (expression_builder,) = expression_builders
        (count,) = unsigned_integers
        self._expression_builders[-1].append(
            PositiveOrMoreExpressionBuilder(expression_builder, count)
        )

    def visit_PositiveRepetitionRangeExpression(  # noqa: N802
        self, match: AnyMatch, /
    ) -> None:
        assert isinstance(match, MatchTree), match
        with (
            self._push_expression_builders() as expression_builders,
            self._push_unsigned_integers() as unsigned_integers,
        ):
            for child in match.children:
                self.visit(child)
        (expression_builder,) = expression_builders
        start, end = unsigned_integers
        self._expression_builders[-1].append(
            PositiveRepetitionRangeExpressionBuilder(
                expression_builder, start, end
            )
        )

    def visit_OptionalExpression(  # noqa: N802
        self, match: AnyMatch, /
    ) -> None:
        assert isinstance(match, MatchTree), match
        with self._push_expression_builders() as expression_builders:
            for child in match.children:
                self.visit(child)
        (expression_builder,) = expression_builders
        self._expression_builders[-1].append(
            OptionalExpressionBuilder(expression_builder)
        )

    def visit_PositiveLookaheadExpression(  # noqa: N802
        self, match: AnyMatch, /
    ) -> None:
        assert isinstance(match, MatchTree), match
        with self._push_expression_builders() as expression_builders:
            for child in match.children:
                self.visit(child)
        (expression_builder,) = expression_builders
        self._expression_builders[-1].append(
            PositiveLookaheadExpressionBuilder(expression_builder)
        )

    def visit_PrioritizedChoiceExpression(  # noqa: N802
        self, match: AnyMatch, /
    ) -> None:
        assert isinstance(match, MatchTree), match
        with self._push_expression_builders() as element_builders:
            for child in match.children:
                self.visit(child)
        self._expression_builders[-1].append(
            PrioritizedChoiceExpressionBuilder(element_builders)
        )

    def visit_Rule(self, match: AnyMatch, /) -> None:  # noqa: N802
        assert isinstance(match, MatchTree), match
        with self._push_expression_builders() as expression_builders:
            for child in match.children:
                self.visit(child)
        rule_name = self._identifiers.pop()
        (expression_builder,) = expression_builders
        self._grammar_builder.add_rule(rule_name, expression_builder)

    def visit_RuleReference(self, match: AnyMatch, /) -> None:  # noqa: N802
        assert isinstance(match, MatchTree), match
        for child in match.children:
            self.visit(child)
        rule_name = self._identifiers.pop()
        self._expression_builders[-1].append(
            self._grammar_builder.get_reference(rule_name)
        )

    def visit_SequenceExpression(  # noqa: N802
        self, match: AnyMatch, /
    ) -> None:
        assert isinstance(match, MatchTree), match
        with self._push_expression_builders() as element_builders:
            for child in match.children:
                self.visit(child)
        self._expression_builders[-1].append(
            SequenceExpressionBuilder(element_builders)
        )

    def visit_SingleQuotedLiteralExpression(  # noqa: N802
        self, match: AnyMatch, /
    ) -> None:
        assert isinstance(match, MatchTree), match
        with self._push_literal_characters() as characters:
            for child in match.children:
                self.visit(child)
        self._expression_builders[-1].append(
            SingleQuotedLiteralExpressionBuilder(''.join(characters))
        )

    def visit_SingleQuotedLiteralExpressionCharacter(  # noqa: N802
        self, match: AnyMatch, /
    ) -> None:
        assert isinstance(match, MatchLeaf | MatchTree), match
        character = match.characters
        character = self._SINGLE_QUOTED_LITERAL_SPECIAL_CHARACTER_MAPPING.get(
            character, character
        )
        assert len(character) == 1, character
        self._literal_characters[-1].append(character)

    def visit_UnsignedInteger(self, match: AnyMatch, /) -> None:  # noqa: N802
        assert isinstance(match, MatchLeaf | MatchTree), match
        value = int(match.characters)
        assert value >= 0, value
        self._unsigned_integers[-1].append(value)

    def visit_ZeroOrMoreExpression(  # noqa: N802
        self, match: AnyMatch, /
    ) -> None:
        assert isinstance(match, MatchTree), match
        with self._push_expression_builders() as expression_builders:
            for child in match.children:
                self.visit(child)
        (expression_builder,) = expression_builders
        self._expression_builders[-1].append(
            ZeroOrMoreExpressionBuilder(expression_builder)
        )

    def visit_ZeroRepetitionRangeExpression(  # noqa: N802
        self, match: AnyMatch, /
    ) -> None:
        assert isinstance(match, MatchTree), match
        with (
            self._push_expression_builders() as expression_builders,
            self._push_unsigned_integers() as unsigned_integers,
        ):
            for child in match.children:
                self.visit(child)
        (expression_builder,) = expression_builders
        (end,) = unsigned_integers
        self._expression_builders[-1].append(
            ZeroRepetitionRangeExpressionBuilder(expression_builder, end)
        )

    @contextlib.contextmanager
    def _push_character_class_characters(self, /) -> Iterator[list[str]]:
        with _push_sublist(self._character_class_characters) as result:
            yield result

    @contextlib.contextmanager
    def _push_character_class_elements(
        self, /
    ) -> Iterator[list[CharacterRange | CharacterSet]]:
        with _push_sublist(self._character_class_elements) as result:
            yield result

    @contextlib.contextmanager
    def _push_expression_builders(
        self, /
    ) -> Iterator[list[ExpressionBuilder[Any, Any]]]:
        with _push_sublist(self._expression_builders) as result:
            yield result

    @contextlib.contextmanager
    def _push_literal_characters(self, /) -> Iterator[list[str]]:
        with _push_sublist(self._literal_characters) as result:
            yield result

    @contextlib.contextmanager
    def _push_unsigned_integers(self, /) -> Iterator[list[int]]:
        with _push_sublist(self._unsigned_integers) as result:
            yield result

    def __init__(self, grammar_builder: GrammarBuilder[Any, Any], /) -> None:
        super().__init__()
        self._grammar_builder = grammar_builder
        self._character_class_characters: list[list[str]] = []
        self._character_class_elements: list[
            list[CharacterRange | CharacterSet]
        ] = []
        self._expression_builders: list[list[ExpressionBuilder[Any, Any]]] = []
        self._identifiers: list[str] = []
        self._literal_characters: list[list[str]] = []
        self._unsigned_integers: list[list[int]] = []


assert (
    len(
        unsupported_classes := [
            cls
            for cls in to_package_non_abstract_subclasses(Expression)  # type: ignore[type-abstract]
            if not callable(
                getattr(TreeToGrammarVisitor, f'visit_{cls.__name__}', None)
            )
        ]
    )
    == 0
), unsupported_classes
assert (
    len(
        unexpected_visitors := [
            name
            for name, field in vars(TreeToGrammarVisitor).items()
            if (
                callable(field)
                and name.startswith(TreeToGrammarVisitor.VISITOR_METHOD_PREFIX)
                and (
                    name.removeprefix(
                        TreeToGrammarVisitor.VISITOR_METHOD_PREFIX
                    )
                    not in list(RuleName)
                )
            )
        ]
    )
    == 0
), unexpected_visitors

_T = TypeVar('_T')


@contextlib.contextmanager
def _push_sublist(nested_list: list[list[_T]], /) -> Iterator[list[_T]]:
    result: list[_T] = []
    nested_list.append(result)
    try:
        yield result
    finally:
        last_expression_builders = nested_list.pop()
        assert last_expression_builders is result
