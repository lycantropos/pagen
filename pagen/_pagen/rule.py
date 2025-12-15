from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, final, overload

from typing_extensions import Self, override

from .expressions import EvaluationResult, Expression
from .match import AnyMatch, MatchT_co
from .mismatch import AnyMismatch, MismatchT_co


class Rule(ABC, Generic[MatchT_co, MismatchT_co]):
    @property
    @abstractmethod
    def expression(self, /) -> Expression[MatchT_co, MismatchT_co]:
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
        cache: dict[str, dict[int, EvaluationResult[AnyMatch, AnyMismatch]]],
        rule_name: str | None,
    ) -> EvaluationResult[MatchT_co, MismatchT_co]:
        raise NotImplementedError

    __slots__ = ()

    @override
    def __str__(self, /) -> str:
        return f'{self.name} <- {self.expression}'


@final
class LeftRecursiveRule(Rule[MatchT_co, MismatchT_co]):
    @property
    @override
    def expression(self, /) -> Expression[MatchT_co, MismatchT_co]:
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
        cache: dict[str, dict[int, EvaluationResult[AnyMatch, AnyMismatch]]],
        rule_name: str | None,
    ) -> EvaluationResult[MatchT_co, MismatchT_co]:
        name = self._name if rule_name is None else rule_name
        name_cache = cache.setdefault(name, {})
        if (result := name_cache.get(index)) is not None:
            assert self._expression.is_valid_result(result), (
                rule_name,
                result,
            )
            return result
        name_cache[index] = self._expression.to_seed_failure(rule_name)
        result = name_cache[index] = self._expression.evaluate(
            text, index, cache=cache, rule_name=name
        )
        result_match = result.match
        if result_match is None:
            return result
        last_characters_count = result_match.characters_count
        while True:
            candidate = self._expression.evaluate(
                text, index, cache=cache, rule_name=name
            )
            candidate_match = candidate.match
            if (
                candidate_match is None
                or candidate_match.characters_count <= last_characters_count
            ):
                break
            result = name_cache[index] = candidate
            last_characters_count = candidate_match.characters_count
        return result

    _expression: Expression[MatchT_co, MismatchT_co]
    _name: str

    __slots__ = '_expression', '_name'

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {LeftRecursiveRule.__qualname__!r} '
            'is not an acceptable base type'
        )

    @override
    def __new__(
        cls, name: str, expression: Expression[MatchT_co, MismatchT_co], /
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
                and self._expression.equals_to(
                    other._expression, visited_rule_names=set()
                )
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
class NonLeftRecursiveRule(Rule[MatchT_co, MismatchT_co]):
    @property
    @override
    def expression(self, /) -> Expression[MatchT_co, MismatchT_co]:
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
        cache: dict[str, dict[int, EvaluationResult[AnyMatch, AnyMismatch]]],
        rule_name: str | None,
    ) -> EvaluationResult[MatchT_co, MismatchT_co]:
        name = self._name if rule_name is None else rule_name
        name_cache = cache.setdefault(name, {})
        if (result := name_cache.get(index)) is not None:
            assert self._expression.is_valid_result(result), (
                rule_name,
                result,
            )
            return result
        result = name_cache[index] = self._expression.evaluate(
            text, index, cache=cache, rule_name=name
        )
        return result

    _expression: Expression[MatchT_co, MismatchT_co]
    _name: str

    __slots__ = '_expression', '_name'

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {NonLeftRecursiveRule.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls, name: str, expression: Expression[MatchT_co, MismatchT_co], /
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
                and self._expression.equals_to(
                    other._expression, visited_rule_names=set()
                )
            )
            if isinstance(other, NonLeftRecursiveRule)
            else NotImplemented
        )

    @override
    def __repr__(self, /) -> str:
        return (
            f'{type(self).__qualname__}({self._name!r}, {self._expression!r})'
        )
