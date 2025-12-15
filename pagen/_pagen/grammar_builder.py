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

    def add_rule(
        self,
        name: str,
        expression_builder: ExpressionBuilder[MatchT_co, MismatchT_co],
        /,
    ) -> None:
        if (
            existing_expression_builder := self._expression_builders.get(name)
        ) is not None:
            raise ValueError(
                f'Rule redefinition is not allowed, '
                f'but for {name!r} tried to replace '
                f'{existing_expression_builder!r} with {expression_builder!r}.'
            )
        self._expression_builders[name] = expression_builder

    def build(self, /) -> Grammar[MatchT_co, MismatchT_co]:
        rules: dict[
            str,
            LeftRecursiveRule[MatchT_co, MismatchT_co]
            | NonLeftRecursiveRule[MatchT_co, MismatchT_co],
        ] = {}
        if (
            len(
                non_terminating_rules := [
                    name
                    for name, builder in self._expression_builders.items()
                    if not builder.is_terminating(set(), is_leftmost=True)
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
        for rule_name, expression_builder in self._expression_builders.items():
            expression = expression_builder.build(rules=rules)
            if expression_builder.is_left_recursive(set()):
                rules[rule_name] = LeftRecursiveRule(rule_name, expression)
            else:
                rules[rule_name] = NonLeftRecursiveRule(rule_name, expression)
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
        return f'{type(self).__qualname__}({self._expression_builders!r})'
