from __future__ import annotations

import sys
from collections.abc import Iterable, Mapping, Sequence
from functools import total_ordering
from typing import Any, ClassVar, TypeAlias, final, overload

from typing_extensions import Self, override

from .expressions import is_failure, is_success
from .match import RuleMatch
from .mismatch import MismatchLeaf, MismatchTree
from .rule import RuleBuilder

if sys.version_info < (3, 11):
    from exceptiongroup import ExceptionGroup

MismatchOriginPath: TypeAlias = Sequence[str]


class Grammar:
    MIN_RULE_BUILDERS_COUNT: ClassVar[int] = 1

    @property
    def rule_names(self, /) -> Sequence[str]:
        return list(self._rule_builders)

    def parse(self, value: str, /, *, starting_rule_name: str) -> RuleMatch:
        rules = {
            rule_name: rule_builder.build()
            for rule_name, rule_builder in self._rule_builders.items()
        }
        result = rules[starting_rule_name].parse(value, 0, rules=rules)
        if is_failure(result):
            grouped_origin_path_with_expected_message_pairs: dict[
                tuple[TextPosition, TextPosition],
                list[tuple[MismatchOriginPath, str]],
            ] = {}
            for (
                start_position,
                stop_position,
                origin_path,
                expected_message,
            ) in sorted(
                _unpack_mismatches(
                    value, result.mismatch, line_separator=self._line_separator
                )
            ):
                assert len(origin_path) > 0, (result, starting_rule_name)
                grouped_origin_path_with_expected_message_pairs.setdefault(
                    (start_position, stop_position), []
                ).append((origin_path, expected_message))
            lines = value.split('\n')
            raise ExceptionGroup(
                (
                    'Failed to parse the input starting '
                    f'with rule {starting_rule_name!r}.'
                ),
                [
                    ParsingError(
                        start_position,
                        stop_position,
                        origin_path_with_expected_message_pairs,
                        lines,
                    )
                    for (
                        start_position,
                        stop_position,
                    ), origin_path_with_expected_message_pairs in (
                        grouped_origin_path_with_expected_message_pairs.items()
                    )
                ],
            )
        assert is_success(result), (starting_rule_name, result)
        match = result.match
        if match.characters_count < len(value):
            raise ValueError(
                f'{value[match.characters_count :]!r} '
                'is unprocessed by the parser'
            )
        assert match.characters_count == len(value), (
            result,
            starting_rule_name,
            value,
        )
        assert match.rule_name == starting_rule_name, (
            result,
            starting_rule_name,
        )
        assert isinstance(match, RuleMatch), (result, starting_rule_name)
        return match

    _line_separator: str | None
    _rule_builders: Mapping[str, RuleBuilder]

    __slots__ = ('_line_separator', '_rule_builders')

    def __new__(
        cls,
        rule_builders: Mapping[str, RuleBuilder],
        /,
        *,
        line_separator: str | None = '\n',
    ) -> Self:
        if not isinstance(rule_builders, Mapping):
            raise TypeError(type(rule_builders))
        if not isinstance(line_separator, str | None):
            raise TypeError(type(line_separator))
        if len(rule_builders) < cls.MIN_RULE_BUILDERS_COUNT:
            raise ValueError(
                f'At least {cls.MIN_RULE_BUILDERS_COUNT!r} '
                'rule builders expected, '
                f'but got {len(rule_builders)!r}.'
            )
        self = super().__new__(cls)
        self._line_separator, self._rule_builders = (
            line_separator,
            rule_builders,
        )
        return self

    @overload
    def __eq__(self, other: Self, /) -> bool: ...

    @overload
    def __eq__(self, other: Any, /) -> Any: ...

    @override
    def __eq__(self, other: Any, /) -> Any:
        return (
            self._rule_builders == other._rule_builders
            if isinstance(other, Grammar)
            else NotImplemented
        )

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._rule_builders!r})'

    @override
    def __str__(self, /) -> str:
        return '\n'.join(map(str, self._rule_builders.values()))


class ParsingError(Exception):
    def __init__(
        self,
        start_position: TextPosition,
        stop_position: TextPosition,
        origin_path_with_expected_message_pairs: Sequence[
            tuple[MismatchOriginPath, str]
        ],
        lines: list[str],
        /,
    ) -> None:
        assert start_position < stop_position, (start_position, stop_position)
        super().__init__()
        self._start_position = start_position
        self._stop_position = stop_position
        self._origin_with_expected_message_pairs = (
            origin_path_with_expected_message_pairs
        )
        self._lines = lines
        assert (
            len(
                self._lines[
                    (
                        self._start_position.line_number - 1
                    ) : self._stop_position.line_number
                ]
            )
            > 0
        ), (start_position, stop_position)

    @override
    def __str__(self, /) -> str:
        return (
            (f'at {self._start_position}-{self._stop_position}' + '\n')
            + '\n'.join(
                [
                    (failed_lines[0] + '\n')
                    + (
                        (' ' * (self._start_position.column_number - 1))
                        + (
                            '^'
                            * (
                                self._stop_position.column_number
                                - self._start_position.column_number
                            )
                        )
                        + '\n'
                    )
                ]
                if (
                    len(
                        failed_lines := self._lines[
                            (
                                self._start_position.line_number - 1
                            ) : self._stop_position.line_number
                        ]
                    )
                    == 1
                )
                else [
                    (failed_lines[0] + '\n')
                    + (
                        (' ' * self._start_position.column_number)
                        + (
                            '^'
                            * (
                                len(failed_lines[0])
                                - self._start_position.column_number
                            )
                        )
                        + '\n'
                    )
                    + (
                        ''.join(
                            (line + '\n') + (('^' * (len(line) + 1)) + '\n')
                            for line in failed_lines[1:-1]
                        )
                    )
                    + (failed_lines[-1] + '\n')
                    + (('^' * (self._stop_position.column_number - 1)) + '\n')
                ]
            )
            + (
                (
                    (
                        ' ' * (self._stop_position.column_number - 2)
                        + '|'
                        + '\n'
                    )
                    + (
                        '+'
                        + '-' * (self._stop_position.column_number - 3)
                        + '+'
                        + '\n'
                    )
                )
                if self._stop_position.column_number > 2
                else ''
            )
            + '\n'.join(
                _format_expected_message(expected_message, origin_descriptions)
                for origin_descriptions, expected_message in (
                    self._origin_with_expected_message_pairs
                )
            )
        )


@final
@total_ordering
class TextPosition:
    @property
    def column_number(self, /) -> int:
        return self._column_number

    @property
    def line_number(self, /) -> int:
        return self._line_number

    _column_number: int
    _line_number: int

    __slots__ = '_column_number', '_line_number'

    @override
    def __new__(cls, line_number: int, column_number: int, /) -> Self:
        assert line_number > 0, line_number
        assert column_number > 0, column_number
        self = super().__new__(cls)
        self._column_number, self._line_number = column_number, line_number
        return self

    @override
    def __eq__(self, other: Any, /) -> Any:
        return (
            (
                self._line_number == other._line_number
                and self._column_number == other._column_number
            )
            if isinstance(other, TextPosition)
            else NotImplemented
        )

    @override
    def __hash__(self, /) -> int:
        return hash((self._line_number, self._column_number))

    def __lt__(self, other: TextPosition, /) -> bool:
        assert isinstance(other, TextPosition), other
        return (self._line_number, self._column_number) < (
            other._line_number,
            other._column_number,
        )

    @override
    def __repr__(self, /) -> str:
        return (
            f'{type(self).__qualname__}'
            '('
            f'{self._line_number!r}, '
            f'{self._column_number!r}'
            ')'
        )

    @override
    def __str__(self, /) -> str:
        return f'{self._line_number}:{self._column_number}'


def _unpack_mismatches(
    text: str,
    value: MismatchLeaf | MismatchTree,
    /,
    *,
    line_separator: str | None,
) -> Iterable[tuple[TextPosition, TextPosition, MismatchOriginPath, str]]:
    if isinstance(value, MismatchTree):
        for child in value.children:
            for (
                start_position,
                stop_position,
                origin_path,
                expected_message,
            ) in _unpack_mismatches(
                text, child, line_separator=line_separator
            ):
                yield (
                    start_position,
                    stop_position,
                    (value.origin_name, *origin_path),
                    expected_message,
                )
        return
    assert isinstance(value, MismatchLeaf)
    if line_separator is not None:
        processed_segment = text[: value.stop_index]
        rest_segment, separator, stop_line_segment = (
            processed_segment.rpartition(line_separator)
        )
        if len(separator) == 0:
            (start_position, stop_position) = (
                TextPosition(1, value.start_index + 1),
                TextPosition(1, value.stop_index + 1),
            )
        else:
            stop_position = TextPosition(
                rest_segment.count(line_separator) + 2,
                len(stop_line_segment) + 1,
            )
            if value.start_index > len(rest_segment):
                start_position = TextPosition(
                    stop_position.line_number,
                    (
                        value.start_index
                        - len(rest_segment)
                        - len(line_separator)
                        + 1
                    ),
                )
            else:
                rest_segment, separator, start_line_segment = rest_segment[
                    : value.start_index
                ].rpartition(line_separator)
                start_position = TextPosition(
                    rest_segment.count(line_separator)
                    + (len(separator) > 0)
                    + 1,
                    len(start_line_segment) + 1,
                )
    else:
        (start_position, stop_position) = (
            TextPosition(1, value.start_index + 1),
            TextPosition(1, value.stop_index + 1),
        )
    yield (
        start_position,
        stop_position,
        (value.origin_name,),
        value.expected_message,
    )


def _format_expected_message(
    expected_message: str,
    origin_path: MismatchOriginPath,
    /,
    *,
    max_line_length: int = 79,
    origin_path_separator: str = ' <- ',
    suffix: str = ')',
) -> str | Any:
    prefix = f'+- expected {expected_message} (from '
    characters_left = max_line_length - (
        len(prefix) + len(suffix) + len(origin_path[-1])
    )
    fitting_origin_paths = [origin_path[-1]]
    for candidate_origin_description in reversed(origin_path[:-1]):
        candidate_origin_description_length = len(origin_path_separator) + len(
            candidate_origin_description
        )
        if characters_left >= candidate_origin_description_length:
            characters_left -= candidate_origin_description_length
            fitting_origin_paths.append(candidate_origin_description)
        else:
            if (
                characters_left <= len(origin_path_separator) + len('...')
                or len(fitting_origin_paths) == 1
            ):
                fitting_origin_paths.append('...')
            else:
                fitting_origin_paths[-1] = '...'
            break
    return (
        ('|' + '\n')
        + prefix
        + origin_path_separator.join(fitting_origin_paths)
        + suffix
    )
