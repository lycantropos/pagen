from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any, final, overload

from typing_extensions import Self, override

from .expressions import (
    EvaluationResult,
    EvaluationSuccess,
    Expression,
    is_failure,
    is_success,
)
from .match import AnyMatch, RuleMatch
from .mismatch import AnyMismatch


class Rule(ABC):
    @property
    @abstractmethod
    def expression(self, /) -> Expression[AnyMatch, AnyMismatch]:
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self, /) -> str:
        raise NotImplementedError

    @abstractmethod
    def parse(
        self,
        text: str,
        index: int,
        /,
        *,
        cache: dict[str, dict[int, EvaluationResult[RuleMatch, AnyMismatch]]],
        rules: Mapping[str, Rule],
    ) -> EvaluationResult[RuleMatch, AnyMismatch]:
        raise NotImplementedError

    __slots__ = ()

    @override
    def __str__(self, /) -> str:
        return f'{self.name} <- {self.expression}'


@final
class LeftRecursiveRule(Rule):
    @property
    @override
    def expression(self, /) -> Expression[AnyMatch, AnyMismatch]:
        return self._expression

    @property
    @override
    def name(self, /) -> str:
        return self._name

    @override
    def parse(
        self,
        text: str,
        index: int,
        /,
        *,
        cache: dict[str, dict[int, EvaluationResult[RuleMatch, AnyMismatch]]],
        rules: Mapping[str, Rule],
    ) -> EvaluationResult[RuleMatch, AnyMismatch]:
        rule_cache = cache.setdefault(self._name, {})
        if (result := rule_cache.get(index)) is not None:
            return result
        rule_cache[index] = self._expression.to_seed_failure(rules=rules)
        result = rule_cache[index] = _expression_result_to_rule_result(
            self._expression.evaluate(text, index, cache=cache, rules=rules),
            rule_name=self._name,
        )
        result_match = result.match
        if result_match is None:
            assert is_failure(result), (self, result)
            return result
        last_characters_count = result_match.characters_count
        while True:
            expression_result = self._expression.evaluate(
                text, index, cache=cache, rules=rules
            )
            candidate_match = expression_result.match
            if (
                candidate_match is None
                or candidate_match.characters_count <= last_characters_count
            ):
                break
            result = rule_cache[index] = _expression_result_to_rule_result(
                expression_result, rule_name=self._name
            )
            last_characters_count = candidate_match.characters_count
        return result

    _expression: Expression[AnyMatch, AnyMismatch]
    _name: str

    __slots__ = '_expression', '_name'

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {LeftRecursiveRule.__qualname__!r} '
            'is not an acceptable base type'
        )

    @override
    def __new__(
        cls, name: str, expression: Expression[AnyMatch, AnyMismatch], /
    ) -> Self:
        self = super().__new__(cls)
        self._expression, self._name = expression, name
        return self

    @overload
    def __eq__(self, other: Self, /) -> bool: ...

    @overload
    def __eq__(self, other: Any, /) -> Any: ...

    @override
    def __eq__(self, other: Any, /) -> Any:
        return (
            (
                self._name == other._name
                and self._expression == other._expression
            )
            if isinstance(other, LeftRecursiveRule)
            else NotImplemented
        )

    @override
    def __repr__(self, /) -> str:
        return (
            f'{type(self).__qualname__}({self._name!r}, {self._expression!r})'
        )


@final
class NonLeftRecursiveRule(Rule):
    @property
    @override
    def expression(self, /) -> Expression[AnyMatch, AnyMismatch]:
        return self._expression

    @property
    @override
    def name(self, /) -> str:
        return self._name

    @override
    def parse(
        self,
        text: str,
        index: int,
        /,
        *,
        cache: dict[str, dict[int, EvaluationResult[RuleMatch, AnyMismatch]]],
        rules: Mapping[str, Rule],
    ) -> EvaluationResult[RuleMatch, AnyMismatch]:
        rule_cache = cache.setdefault(self._name, {})
        if (result := rule_cache.get(index)) is not None:
            assert (
                not is_success(result) or result.match.rule_name == self._name
            )
            return result
        result = rule_cache[index] = _expression_result_to_rule_result(
            self._expression.evaluate(text, index, cache=cache, rules=rules),
            rule_name=self._name,
        )
        return result

    _expression: Expression[AnyMatch, AnyMismatch]
    _name: str

    __slots__ = '_expression', '_name'

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {NonLeftRecursiveRule.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls, name: str, expression: Expression[AnyMatch, AnyMismatch], /
    ) -> Self:
        self = super().__new__(cls)
        self._expression, self._name = expression, name
        return self

    @overload
    def __eq__(self, other: Self, /) -> bool: ...

    @overload
    def __eq__(self, other: Any, /) -> Any: ...

    @override
    def __eq__(self, other: Any, /) -> Any:
        return (
            (
                self._name == other._name
                and self._expression == other._expression
            )
            if isinstance(other, NonLeftRecursiveRule)
            else NotImplemented
        )

    @override
    def __repr__(self, /) -> str:
        return (
            f'{type(self).__qualname__}({self._name!r}, {self._expression!r})'
        )


def _expression_result_to_rule_result(
    expression_result: EvaluationResult[AnyMatch, AnyMismatch],
    /,
    *,
    rule_name: str,
) -> EvaluationResult[RuleMatch, AnyMismatch]:
    if is_success(expression_result):
        return EvaluationSuccess(
            RuleMatch(rule_name, match=expression_result.match),
            expression_result.mismatch,
        )
    assert is_failure(expression_result), expression_result
    return expression_result
