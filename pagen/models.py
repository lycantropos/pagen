from typing import get_args

from . import _pagen as _module

# character containers
CharacterRange = _module.CharacterRange
CharacterSet = _module.CharacterSet

# expressions
AnyCharacterExpression = _module.AnyCharacterExpression
CharacterClassExpression = _module.CharacterClassExpression
ComplementedCharacterClassExpression = (
    _module.ComplementedCharacterClassExpression
)
DoubleQuotedLiteralExpression = _module.DoubleQuotedLiteralExpression
ExactRepetitionExpression = _module.ExactRepetitionExpression
NegativeLookaheadExpression = _module.NegativeLookaheadExpression
OneOrMoreExpression = _module.OneOrMoreExpression
OptionalExpression = _module.OptionalExpression
PositiveLookaheadExpression = _module.PositiveLookaheadExpression
PositiveOrMoreExpression = _module.PositiveOrMoreExpression
PositiveRepetitionRangeExpression = _module.PositiveRepetitionRangeExpression
PrioritizedChoiceExpression = _module.PrioritizedChoiceExpression
RuleReference = _module.RuleReference
SequenceExpression = _module.SequenceExpression
SingleQuotedLiteralExpression = _module.SingleQuotedLiteralExpression
ZeroOrMoreExpression = _module.ZeroOrMoreExpression
ZeroRepetitionRangeExpression = _module.ZeroRepetitionRangeExpression

Expression = (
    AnyCharacterExpression
    | CharacterClassExpression
    | DoubleQuotedLiteralExpression
    | ExactRepetitionExpression
    | NegativeLookaheadExpression
    | OneOrMoreExpression
    | OptionalExpression
    | PositiveLookaheadExpression
    | PositiveOrMoreExpression
    | PositiveRepetitionRangeExpression
    | PrioritizedChoiceExpression
    | RuleReference
    | SequenceExpression
    | SingleQuotedLiteralExpression
    | ZeroOrMoreExpression
    | ZeroRepetitionRangeExpression
)

assert (
    len(
        missing_expression_classes := [
            cls
            for cls in get_args(Expression)
            if cls is not globals().get(cls.__name__)
        ]
    )
    == 0
), missing_expression_classes

# grammar
Grammar = _module.Grammar
GrammarBuilder = _module.GrammarBuilder
LeftRecursiveRule = _module.LeftRecursiveRule
NonLeftRecursiveRule = _module.NonLeftRecursiveRule
Rule = _module.Rule

# matches
LookaheadMatch = _module.LookaheadMatch
MatchLeaf = _module.MatchLeaf
MatchTree = _module.MatchTree

# mismatches
MismatchLeaf = _module.MismatchLeaf
MismatchTree = _module.MismatchTree
