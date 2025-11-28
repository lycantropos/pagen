from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Generic, overload

from typing_extensions import Self, override

from .match import MatchT_co
from .mismatch import MismatchT_co, is_mismatch
from .rule import Rule


class Grammar(Generic[MatchT_co, MismatchT_co]):
    @property
    def rules(self, /) -> Mapping[str, Rule[MatchT_co, MismatchT_co]]:
        return self._rules

    __slots__ = ('_rules',)

    def __new__(
        cls, rules: Mapping[str, Rule[MatchT_co, MismatchT_co]], /
    ) -> Self:
        self = super().__new__(cls)
        self._rules = rules
        return self

    def parse(self, value: str, /, *, starting_rule_name: str) -> MatchT_co:
        result = self._rules[starting_rule_name].parse(
            value, 0, cache={}, rule_name=None
        )
        if is_mismatch(result):
            raise ValueError(result)
        if result.characters_count < len(value):
            raise ValueError(
                f'{value[result.characters_count :]!r} '
                'is unprocessed by the parser'
            )
        assert result.characters_count == len(value), (result, value)
        return result

    _rules: Mapping[str, Rule[MatchT_co, MismatchT_co]]

    @overload
    def __eq__(self, other: Self, /) -> bool: ...

    @overload
    def __eq__(self, other: Any, /) -> Any: ...

    @override
    def __eq__(self, other: Any, /) -> Any:
        return (
            self._rules == other._rules
            if isinstance(other, Grammar)
            else NotImplemented
        )

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._rules!r})'

    @override
    def __str__(self, /) -> str:
        return '\n'.join(map(str, self._rules.values()))
