from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Generic, overload

from typing_extensions import Self, override

from .expressions import is_failure, is_success
from .match import MatchT_co
from .mismatch import MismatchLeaf, MismatchT_co, MismatchTree
from .rule import Rule


class Grammar(Generic[MatchT_co, MismatchT_co]):
    @property
    def rules(self, /) -> Mapping[str, Rule[MatchT_co, MismatchT_co]]:
        return self._rules

    def parse(self, value: str, /, *, starting_rule_name: str) -> MatchT_co:
        result = self._rules[starting_rule_name].parse(
            value, 0, cache={}, rule_name=None
        )
        if is_failure(result):
            raise ValueError(
                '\n'
                + '\n'.join(
                    self._mismatch_to_strings(value, result.mismatch, depth=0)
                )
            )
        assert is_success(result), (starting_rule_name, result)
        match = result.match
        if match.characters_count < len(value):
            raise ValueError(
                f'{value[match.characters_count :]!r} '
                'is unprocessed by the parser'
            )
        assert match.characters_count == len(value), (result, value)
        return match

    _rules: Mapping[str, Rule[MatchT_co, MismatchT_co]]

    def _mismatch_to_strings(
        self, text: str, value: MismatchLeaf | MismatchTree, /, *, depth: int
    ) -> list[str]:
        unit_space = '  '
        if isinstance(value, MismatchTree):
            result = [f'{depth * unit_space}{value.origin_description}:']
            for child in value.children:
                result.extend(
                    self._mismatch_to_strings(text, child, depth=depth + 1)
                )
            return result
        assert isinstance(value, MismatchLeaf)
        return [
            f'{depth * unit_space}{value.origin_description}: '
            f'expected {value.expected_message}, '
            f'got {text[value.start_index : value.stop_index]!r}'
        ]

    __slots__ = ('_rules',)

    def __new__(
        cls, rules: Mapping[str, Rule[MatchT_co, MismatchT_co]], /
    ) -> Self:
        self = super().__new__(cls)
        self._rules = rules
        return self

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
