from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
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


@final
class RuleData:
    @property
    def expression(self, /) -> Expression[AnyMatch, AnyMismatch]:
        return self._expression

    @property
    def name(self, /) -> str:
        return self._name

    _expression: Expression[AnyMatch, AnyMismatch]
    _name: str

    __slots__ = '_expression', '_name'

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
            if isinstance(other, RuleData)
            else NotImplemented
        )

    @override
    def __repr__(self, /) -> str:
        return (
            f'{type(self).__qualname__}({self._name!r}, {self._expression!r})'
        )


class RuleBuilder(ABC):
    @property
    @abstractmethod
    def expression(self, /) -> Expression[AnyMatch, AnyMismatch]:
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self, /) -> str:
        raise NotImplementedError

    @abstractmethod
    def build(self, /) -> Rule:
        raise NotImplementedError

    __slots__ = ()

    @override
    def __str__(self, /) -> str:
        return f'{self.name} <- {self.expression}'


@final
class LeftRecursiveRuleBuilder(RuleBuilder):
    @property
    @override
    def expression(self, /) -> Expression[AnyMatch, AnyMismatch]:
        return self._data.expression

    @property
    @override
    def name(self, /) -> str:
        return self._data.name

    @override
    def build(self, /) -> LeftRecursiveRule:
        return LeftRecursiveRule(self._data, cache={})

    _data: RuleData

    __slots__ = ('_data',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {LeftRecursiveRuleBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls, name: str, expression: Expression[AnyMatch, AnyMismatch], /
    ) -> Self:
        self = super().__new__(cls)
        self._data = RuleData(name, expression)
        return self

    @overload
    def __eq__(self, other: Self, /) -> bool: ...

    @overload
    def __eq__(self, other: Any, /) -> Any: ...

    @override
    def __eq__(self, other: Any, /) -> Any:
        return (
            self._data == other._data
            if isinstance(other, LeftRecursiveRuleBuilder)
            else NotImplemented
        )

    @override
    def __repr__(self, /) -> str:
        return (
            f'{type(self).__qualname__}'
            '('
            f'{self._data.name!r}, {self._data.expression!r}'
            ')'
        )


@final
class NonLeftRecursiveRuleBuilder(RuleBuilder):
    @property
    @override
    def expression(self, /) -> Expression[AnyMatch, AnyMismatch]:
        return self._data.expression

    @property
    @override
    def name(self, /) -> str:
        return self._data.name

    @override
    def build(self, /) -> NonLeftRecursiveRule:
        return NonLeftRecursiveRule(self._data, cache={})

    _data: RuleData

    __slots__ = ('_data',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {NonLeftRecursiveRuleBuilder.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls, name: str, expression: Expression[AnyMatch, AnyMismatch], /
    ) -> Self:
        self = super().__new__(cls)
        self._data = RuleData(name, expression)
        return self

    @overload
    def __eq__(self, other: Self, /) -> bool: ...

    @overload
    def __eq__(self, other: Any, /) -> Any: ...

    @override
    def __eq__(self, other: Any, /) -> Any:
        return (
            self._data == other._data
            if isinstance(other, NonLeftRecursiveRuleBuilder)
            else NotImplemented
        )

    @override
    def __repr__(self, /) -> str:
        return (
            f'{type(self).__qualname__}'
            '('
            f'{self._data.name!r}, {self._data.expression!r}'
            ')'
        )


class Rule(ABC):
    @property
    @abstractmethod
    def expression(self, /) -> Expression[AnyMatch, AnyMismatch]:
        raise NotImplementedError

    @abstractmethod
    def parse(
        self, text: str, index: int, /, *, rules: Sequence[Rule]
    ) -> EvaluationResult[RuleMatch, AnyMismatch]:
        raise NotImplementedError

    __slots__ = ()


@final
class LeftRecursiveRule(Rule):
    @property
    @override
    def expression(self, /) -> Expression[AnyMatch, AnyMismatch]:
        return self._data.expression

    @override
    def parse(
        self, text: str, index: int, /, *, rules: Sequence[Rule]
    ) -> EvaluationResult[RuleMatch, AnyMismatch]:
        cache = self._cache
        if (result := cache.get(index)) is not None:
            return result
        expression, name = self._data.expression, self._data.name
        cache[index] = expression.to_seed_failure(rules=rules)
        result = cache[index] = _expression_result_to_rule_result(
            expression.evaluate(text, index, rules=rules), rule_name=name
        )
        result_match = result.match
        if result_match is None:
            assert is_failure(result), (self, result)
            return result
        last_characters_count = result_match.characters_count
        while True:
            expression_result = expression.evaluate(text, index, rules=rules)
            expression_match = expression_result.match
            if (
                expression_match is None
                or expression_match.characters_count <= last_characters_count
            ):
                break
            result = cache[index] = _expression_result_to_rule_result(
                expression_result, rule_name=name
            )
            last_characters_count = expression_match.characters_count
        return result

    _cache: dict[int, EvaluationResult[RuleMatch, AnyMismatch]]
    _data: RuleData

    __slots__ = '_cache', '_data'

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {LeftRecursiveRule.__qualname__!r} '
            'is not an acceptable base type'
        )

    @override
    def __new__(
        cls,
        data: RuleData,
        /,
        *,
        cache: dict[int, EvaluationResult[RuleMatch, AnyMismatch]],
    ) -> Self:
        self = super().__new__(cls)
        self._cache, self._data = cache, data
        return self

    @overload
    def __eq__(self, other: Self, /) -> bool: ...

    @overload
    def __eq__(self, other: Any, /) -> Any: ...

    @override
    def __eq__(self, other: Any, /) -> Any:
        return (
            (self._data == other._data and self._cache == other._cache)
            if isinstance(other, LeftRecursiveRule)
            else NotImplemented
        )

    @override
    def __repr__(self, /) -> str:
        return (
            f'{type(self).__qualname__}({self._data!r}, cache={self._cache!r})'
        )


@final
class NonLeftRecursiveRule(Rule):
    @property
    @override
    def expression(self, /) -> Expression[AnyMatch, AnyMismatch]:
        return self._data.expression

    @override
    def parse(
        self, text: str, index: int, /, *, rules: Sequence[Rule]
    ) -> EvaluationResult[RuleMatch, AnyMismatch]:
        rule_cache = self._cache
        if (result := rule_cache.get(index)) is not None:
            assert (
                not is_success(result)
                or result.match.rule_name == self._data.name
            )
            return result
        result = rule_cache[index] = _expression_result_to_rule_result(
            self._data.expression.evaluate(text, index, rules=rules),
            rule_name=self._data.name,
        )
        return result

    _cache: dict[int, EvaluationResult[RuleMatch, AnyMismatch]]
    _data: RuleData

    __slots__ = '_cache', '_data'

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {NonLeftRecursiveRule.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls,
        data: RuleData,
        /,
        *,
        cache: dict[int, EvaluationResult[RuleMatch, AnyMismatch]],
    ) -> Self:
        self = super().__new__(cls)
        self._cache, self._data = cache, data
        return self

    @overload
    def __eq__(self, other: Self, /) -> bool: ...

    @overload
    def __eq__(self, other: Any, /) -> Any: ...

    @override
    def __eq__(self, other: Any, /) -> Any:
        return (
            (self._data == other._data and self._cache == other._cache)
            if isinstance(other, NonLeftRecursiveRule)
            else NotImplemented
        )

    @override
    def __repr__(self, /) -> str:
        return (
            f'{type(self).__qualname__}({self._data!r}, cache={self._cache!r})'
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
