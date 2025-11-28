from __future__ import annotations

from collections.abc import Mapping
from typing import Generic

from typing_extensions import override

from .expression_builders import ExpressionBuilder, RuleReferenceBuilder
from .grammar import Grammar
from .match import MatchT_co
from .mismatch import MismatchT_co
from .rule import LeftRecursiveRule, NonLeftRecursiveRule


class GrammarBuilder(Generic[MatchT_co, MismatchT_co]):
    @property
    def expression_builders(
        self, /
    ) -> Mapping[str, ExpressionBuilder[MatchT_co, MismatchT_co]]:
        return self._expression_builders

    def add_expression_builder(
        self,
        name: str,
        expression_builder: ExpressionBuilder[MatchT_co, MismatchT_co],
        /,
    ) -> None:
        assert name not in self._expression_builders, (
            self._expression_builders[name],
            expression_builder,
        )
        self._expression_builders[name] = expression_builder

    def build(self, /) -> Grammar[MatchT_co, MismatchT_co]:
        rules: dict[
            str,
            LeftRecursiveRule[MatchT_co, MismatchT_co]
            | NonLeftRecursiveRule[MatchT_co, MismatchT_co],
        ] = {}
        for name, builder in self._expression_builders.items():
            expression = builder.build(rules=rules)
            if builder.is_left_recursive(set()):
                rules[name] = LeftRecursiveRule(name, expression)
            else:
                rules[name] = NonLeftRecursiveRule(name, expression)
        return Grammar(rules)

    def get_reference(
        self, name: str, /
    ) -> RuleReferenceBuilder[MatchT_co, MismatchT_co]:
        return RuleReferenceBuilder(
            name, expression_builders=self._expression_builders
        )

    _expression_builders: dict[str, ExpressionBuilder[MatchT_co, MismatchT_co]]

    def __init__(
        self,
        expression_builders: (
            dict[str, ExpressionBuilder[MatchT_co, MismatchT_co]] | None
        ) = None,
        /,
    ) -> None:
        self._expression_builders = expression_builders or {}

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression_builders})'
