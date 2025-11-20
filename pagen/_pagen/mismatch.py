from __future__ import annotations

from typing import Any, final

from typing_extensions import Self, TypeIs, override


@final
class Mismatch:
    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {Mismatch.__qualname__!r} is not an acceptable base type'
        )

    @override
    def __new__(cls, rule_name: str | None, index: int, /) -> Self:
        self = super().__new__(cls)
        self._index, self._rule_name = index, rule_name
        return self

    _index: int
    _rule_name: str | None

    @override
    def __repr__(self, /) -> str:
        return (
            f'{type(self).__qualname__}({self._rule_name!r}, {self._index!r})'
        )


def is_mismatch(value: Any, /) -> TypeIs[Mismatch]:
    return isinstance(value, Mismatch)
