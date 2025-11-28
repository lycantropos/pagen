from . import _pagen as _module
from ._utils import to_package_non_abstract_subclasses

# character containers
CharacterRange = _module.CharacterRange
CharacterSet = _module.CharacterSet

# expressions
Expression = _module.Expression
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

assert (
    len(
        missing_expression_classes := [
            cls
            for cls in to_package_non_abstract_subclasses(Expression)  # type: ignore[type-abstract]
            if cls is not globals().get(cls.__name__)
        ]
    )
    == 0
), missing_expression_classes

# expression builders
ExpressionBuilder = _module.ExpressionBuilder
AnyCharacterExpressionBuilder = _module.AnyCharacterExpressionBuilder
DoubleQuotedLiteralExpressionBuilder = (
    _module.DoubleQuotedLiteralExpressionBuilder
)
CharacterClassExpressionBuilder = _module.CharacterClassExpressionBuilder
ComplementedCharacterClassExpressionBuilder = (
    _module.ComplementedCharacterClassExpressionBuilder
)
ExactRepetitionExpressionBuilder = _module.ExactRepetitionExpressionBuilder
PositiveOrMoreExpressionBuilder = _module.PositiveOrMoreExpressionBuilder
PositiveRepetitionRangeExpressionBuilder = (
    _module.PositiveRepetitionRangeExpressionBuilder
)
ZeroRepetitionRangeExpressionBuilder = (
    _module.ZeroRepetitionRangeExpressionBuilder
)
SingleQuotedLiteralExpressionBuilder = (
    _module.SingleQuotedLiteralExpressionBuilder
)
NegativeLookaheadExpressionBuilder = _module.NegativeLookaheadExpressionBuilder
OneOrMoreExpressionBuilder = _module.OneOrMoreExpressionBuilder
OptionalExpressionBuilder = _module.OptionalExpressionBuilder
PositiveLookaheadExpressionBuilder = _module.PositiveLookaheadExpressionBuilder
PrioritizedChoiceExpressionBuilder = _module.PrioritizedChoiceExpressionBuilder
RuleReferenceBuilder = _module.RuleReferenceBuilder
SequenceExpressionBuilder = _module.SequenceExpressionBuilder
ZeroOrMoreExpressionBuilder = _module.ZeroOrMoreExpressionBuilder

assert (
    len(
        missing_expression_builder_classes := [
            cls
            for cls in to_package_non_abstract_subclasses(ExpressionBuilder)  # type: ignore[type-abstract]
            if cls is not globals().get(cls.__name__)
        ]
    )
    == 0
), missing_expression_builder_classes

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
