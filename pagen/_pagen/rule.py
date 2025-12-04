from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, overload

from typing_extensions import Self, override

from .expressions import Expression
from .match import AnyMatch, MatchT_co
from .mismatch import AnyMismatch, MismatchT_co, is_mismatch


class Rule(ABC, Generic[MatchT_co, MismatchT_co]):
    __slots__ = ()

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
        cache: dict[str, dict[int, AnyMatch | AnyMismatch]],
        rule_name: str | None,
    ) -> MatchT_co | MismatchT_co:
        raise NotImplementedError

    @override
    def __str__(self, /) -> str:
        return f'{self.name} <- {self.expression}'


class LeftRecursiveRule(Rule[MatchT_co, MismatchT_co]):
    __slots__ = '_expression', '_name'

    def __new__(
        cls, name: str, expression: Expression[MatchT_co, MismatchT_co], /
    ) -> Self:
        self = super().__new__(cls)
        self._expression, self._name = expression, name
        return self

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
        cache: dict[str, dict[int, AnyMatch | AnyMismatch]],
        rule_name: str | None,
    ) -> MatchT_co | MismatchT_co:
        name = self._name if rule_name is None else rule_name
        name_cache = cache.setdefault(name, {})
        if (match := name_cache.get(index)) is not None:
            assert self._expression.is_valid_mismatch(
                match
            ) or self._expression.is_valid_match(match), match
            return match
        name_cache[index] = self._expression.to_seed_mismatch(rule_name)
        result = name_cache[index] = self._expression.evaluate(
            text, index, cache=cache, rule_name=name
        )
        if is_mismatch(result):
            return result
        last_characters_count = result.characters_count
        while True:
            candidate = self._expression.evaluate(
                text, index, cache=cache, rule_name=name
            )
            if (
                is_mismatch(candidate)
                or candidate.characters_count <= last_characters_count
            ):
                break
            result = name_cache[index] = candidate
            last_characters_count = candidate.characters_count
        return result

    _expression: Expression[MatchT_co, MismatchT_co]
    _name: str

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


class NonLeftRecursiveRule(Rule[MatchT_co, MismatchT_co]):
    __slots__ = '_expression', '_name'

    def __new__(
        cls, name: str, expression: Expression[MatchT_co, MismatchT_co], /
    ) -> Self:
        self = super().__new__(cls)
        self._expression, self._name = expression, name
        return self

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
        cache: dict[str, dict[int, AnyMatch | AnyMismatch]],
        rule_name: str | None,
    ) -> MatchT_co | MismatchT_co:
        name = self._name if rule_name is None else rule_name
        name_cache = cache.setdefault(name, {})
        if (match := name_cache.get(index)) is not None:
            assert self.expression.is_valid_mismatch(
                match
            ) or self.expression.is_valid_match(match), match
            return match
        result = name_cache[index] = self._expression.evaluate(
            text, index, cache=cache, rule_name=name
        )
        return result

    _expression: Expression[MatchT_co, MismatchT_co]
    _name: str

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
