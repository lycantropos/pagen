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
SingleQuotedLiteralExpression = _module.SingleQuotedLiteralExpression
NegativeLookaheadExpression = _module.NegativeLookaheadExpression
OneOrMoreExpression = _module.OneOrMoreExpression
OptionalExpression = _module.OptionalExpression
PositiveLookaheadExpression = _module.PositiveLookaheadExpression
PrioritizedChoiceExpression = _module.PrioritizedChoiceExpression
RuleReference = _module.RuleReference
SequenceExpression = _module.SequenceExpression
ZeroOrMoreExpression = _module.ZeroOrMoreExpression

assert (
    len(
        missing_classes := [
            cls.__name__
            for cls in to_package_non_abstract_subclasses(Expression)  # type: ignore[type-abstract]
            if cls is not globals().get(cls.__name__)
        ]
    )
    == 0
), missing_classes

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
        missing_classes := [
            cls.__name__
            for cls in to_package_non_abstract_subclasses(ExpressionBuilder)  # type: ignore[type-abstract]
            if cls is not globals().get(cls.__name__)
        ]
    )
    == 0
), missing_classes

# grammar
Grammar = _module.Grammar
GrammarBuilder = _module.GrammarBuilder
Rule = _module.Rule

# matches
LookaheadMatch = _module.LookaheadMatch
MatchLeaf = _module.MatchLeaf
MatchTree = _module.MatchTree
