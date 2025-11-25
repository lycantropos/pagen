from __future__ import annotations

from _operator import methodcaller
from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping, Sequence
from types import MappingProxyType
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Generic,
    TypeGuard,
    final,
    overload,
)

from typing_extensions import Self, TypeIs, override

from .character_containers import (
    CharacterRange,
    CharacterSet,
    merge_consecutive_character_sets,
)
from .constants import (
    COMMON_SPECIAL_CHARACTERS_TRANSLATION_TABLE,
    DOUBLE_QUOTED_LITERAL_SPECIAL_CHARACTERS,
    SINGLE_QUOTED_LITERAL_SPECIAL_CHARACTERS,
)
from .match import AnyMatch, LookaheadMatch, MatchLeaf, MatchT_co, MatchTree
from .mismatch import Mismatch, is_mismatch

if TYPE_CHECKING:
    from .rule import Rule


class Expression(ABC, Generic[MatchT_co]):
    __slots__ = ()

    @abstractmethod
    def equals_to(
        self, other: Expression[Any], /, *, visited_rule_names: set[str]
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def evaluate(
        self,
        text: str,
        index: int,
        /,
        *,
        cache: dict[str, dict[int, AnyMatch | Mismatch]],
        rule_name: str | None,
    ) -> MatchT_co | Mismatch:
        raise NotImplementedError

    def is_valid_match(self, match: Any, /) -> TypeGuard[MatchT_co]:
        return any(
            isinstance(match, match_cls)
            for match_cls in self.to_match_classes()
        )

    @abstractmethod
    def to_match_classes(self, /) -> Iterable[type[MatchT_co]]:
        raise NotImplementedError

    @abstractmethod
    def to_nested_str(self, /) -> str:
        raise NotImplementedError

    @overload
    def __eq__(self, other: Self, /) -> bool: ...

    @overload
    def __eq__(self, other: Any, /) -> Any: ...

    @override
    def __eq__(self, other: Any, /) -> Any:
        return (
            self.equals_to(other, visited_rule_names=set())
            if isinstance(other, Expression)
            else NotImplemented
        )

    @abstractmethod
    def __str__(self, /) -> str:
        raise NotImplementedError

    @abstractmethod
    def __repr__(self, /) -> str:
        raise NotImplementedError


class AnyCharacterExpression(Expression[MatchLeaf]):
    __slots__ = ()

    @override
    def equals_to(
        self, other: Expression[Any], /, *, visited_rule_names: set[str]
    ) -> bool:
        return isinstance(other, AnyCharacterExpression)

    @override
    def evaluate(
        self,
        text: str,
        index: int,
        /,
        *,
        cache: dict[str, dict[int, AnyMatch | Mismatch]],
        rule_name: str | None,
    ) -> MatchLeaf | Mismatch:
        return (
            MatchLeaf(rule_name, characters=text[index])
            if index < len(text)
            else Mismatch(rule_name, index)
        )

    @override
    def to_match_classes(self, /) -> Iterable[type[MatchLeaf]]:
        yield MatchLeaf

    @override
    def to_nested_str(self, /) -> str:
        return self.__str__()

    @override
    def __str__(self, /) -> str:
        return '.'

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}()'


@final
class CharacterClassExpression(Expression[MatchLeaf]):
    MIN_ELEMENTS_COUNT: ClassVar[int] = 1

    __slots__ = ('_elements',)

    def __new__(
        cls, elements: Sequence[CharacterRange | CharacterSet], /
    ) -> Self:
        if len(elements) < cls.MIN_ELEMENTS_COUNT:
            raise ValueError(
                'Character class should have '
                f'at least {cls.MIN_ELEMENTS_COUNT!r} elements, '
                f'but got {elements!r}.'
            )
        self = super().__new__(cls)
        self._elements = merge_consecutive_character_sets(elements)
        return self

    @override
    def equals_to(
        self, other: Expression[Any], /, *, visited_rule_names: set[str]
    ) -> bool:
        return (
            isinstance(other, CharacterClassExpression)
            and self._elements == other._elements  # noqa: SLF001
        )

    @override
    def evaluate(
        self,
        text: str,
        index: int,
        /,
        *,
        cache: dict[str, dict[int, AnyMatch | Mismatch]],
        rule_name: str | None,
    ) -> MatchLeaf | Mismatch:
        if index >= len(text):
            return Mismatch(rule_name, index)
        character = text[index]
        return (
            MatchLeaf(rule_name, characters=character)
            if any(character in element for element in self._elements)
            else Mismatch(rule_name, index)
        )

    @override
    def to_match_classes(self, /) -> Iterable[type[MatchLeaf]]:
        yield MatchLeaf

    @override
    def to_nested_str(self, /) -> str:
        return self.__str__()

    _elements: Sequence[CharacterRange | CharacterSet]

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._elements!r})'

    @override
    def __str__(self, /) -> str:
        return f'[{"".join(map(str, self._elements))}]'


class ComplementedCharacterClassExpression(Expression[MatchLeaf]):
    MIN_ELEMENTS_COUNT: ClassVar[int] = 1

    __slots__ = ('_elements',)

    def __new__(
        cls, elements: Sequence[CharacterRange | CharacterSet], /
    ) -> Self:
        if len(elements) < cls.MIN_ELEMENTS_COUNT:
            raise ValueError(
                'Complemented character class should have '
                f'at least {cls.MIN_ELEMENTS_COUNT!r} elements, '
                f'but got {elements!r}.'
            )
        self = super().__new__(cls)
        self._elements = merge_consecutive_character_sets(elements)
        return self

    @override
    def equals_to(
        self, other: Expression[Any], /, *, visited_rule_names: set[str]
    ) -> bool:
        return (
            isinstance(other, ComplementedCharacterClassExpression)
            and self._elements == other._elements  # noqa: SLF001
        )

    @override
    def evaluate(
        self,
        text: str,
        index: int,
        /,
        *,
        cache: dict[str, dict[int, AnyMatch | Mismatch]],
        rule_name: str | None,
    ) -> MatchLeaf | Mismatch:
        if index >= len(text):
            return Mismatch(rule_name, index)
        character = text[index]
        return (
            MatchLeaf(rule_name, characters=character)
            if all(character not in element for element in self._elements)
            else Mismatch(rule_name, index)
        )

    @override
    def to_match_classes(self, /) -> Iterable[type[MatchLeaf]]:
        yield MatchLeaf

    @override
    def to_nested_str(self, /) -> str:
        return self.__str__()

    _elements: Sequence[CharacterRange | CharacterSet]

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._elements!r})'

    @override
    def __str__(self, /) -> str:
        return f'[^{"".join(map(str, self._elements))}]'


class ExactRepetitionExpression(Expression[MatchTree]):
    MIN_COUNT: ClassVar[int] = 2

    __slots__ = '_count', '_expression'

    def __new__(
        cls, expression: Expression[MatchLeaf | MatchTree], count: int, /
    ) -> Self:
        _validate_repetition_bound(count)
        _validate_expression(expression)
        _validate_progressing_expression(expression)
        if count < cls.MIN_COUNT:
            raise ValueError(
                f'Repetition count should not be less than {cls.MIN_COUNT!r}, '
                f'but got {count!r}.'
            )
        self = super().__new__(cls)
        self._count, self._expression = count, expression
        return self

    @override
    def equals_to(
        self, other: Expression[Any], /, *, visited_rule_names: set[str]
    ) -> bool:
        return (
            isinstance(other, ExactRepetitionExpression)
            and self._count == other._count
            and self._expression.equals_to(
                other._expression, visited_rule_names=visited_rule_names
            )
        )

    @override
    def evaluate(
        self,
        text: str,
        index: int,
        /,
        *,
        cache: dict[str, dict[int, AnyMatch | Mismatch]],
        rule_name: str | None,
    ) -> MatchTree | Mismatch:
        children: list[MatchLeaf | MatchTree] = []
        expression = self._expression
        start_index = index
        for _ in range(self._count):
            if not is_mismatch(
                match := expression.evaluate(
                    text, index, cache=cache, rule_name=None
                )
            ):
                assert isinstance(match, MatchLeaf | MatchTree)
                children.append(match)
                index += match.characters_count
            else:
                return Mismatch(rule_name, start_index)
        return MatchTree(rule_name, children=children)

    @override
    def to_match_classes(self, /) -> Iterable[type[MatchTree]]:
        yield MatchTree

    @override
    def to_nested_str(self, /) -> str:
        return f'({self.__str__()})'

    _count: int
    _expression: Expression[MatchLeaf | MatchTree]

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression!r})'

    @override
    def __str__(self, /) -> str:
        return f'{self._expression.to_nested_str()}{{{self._count}}}'


class LiteralExpression(Expression[MatchLeaf]):
    MIN_CHARACTERS_COUNT: ClassVar[int] = 1

    __slots__ = ()

    @property
    @abstractmethod
    def characters(self, /) -> str:
        pass

    @override
    def equals_to(
        self, other: Expression[Any], /, *, visited_rule_names: set[str]
    ) -> bool:
        return (
            isinstance(other, type(self))
            and self.characters == other.characters
        )

    @override
    def evaluate(
        self,
        text: str,
        index: int,
        /,
        *,
        cache: dict[str, dict[int, AnyMatch | Mismatch]],
        rule_name: str | None,
    ) -> MatchLeaf | Mismatch:
        return (
            MatchLeaf(rule_name, characters=self.characters)
            if text[index : index + len(self.characters)] == self.characters
            else Mismatch(rule_name, index)
        )

    @override
    def to_match_classes(self, /) -> Iterable[type[MatchLeaf]]:
        yield MatchLeaf

    @override
    def to_nested_str(self, /) -> str:
        return self.__str__()

    @classmethod
    def _validate_characters(cls, value: str, /) -> None:
        if not isinstance(value, str):
            raise TypeError(type(value))
        if len(value) < cls.MIN_CHARACTERS_COUNT:
            raise ValueError(
                'Literal should have '
                f'at least {cls.MIN_CHARACTERS_COUNT} characters, '
                f'but got {value!r}.'
            )

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self.characters!r})'


class DoubleQuotedLiteralExpression(LiteralExpression):
    __slots__ = ('_characters',)

    def __new__(cls, characters: str, /) -> Self:
        cls._validate_characters(characters)
        self = super().__new__(cls)
        self._characters = characters
        return self

    @property
    def characters(self, /) -> str:
        return self._characters

    _characters: str

    @override
    def __str__(self, /) -> str:
        return (
            f'"{_escape_double_quoted_literal_characters(self._characters)}"'
        )


class SingleQuotedLiteralExpression(LiteralExpression):
    __slots__ = ('_characters',)

    def __new__(cls, characters: str, /) -> Self:
        cls._validate_characters(characters)
        self = super().__new__(cls)
        self._characters = characters
        return self

    @property
    def characters(self, /) -> str:
        return self._characters

    _characters: str

    @override
    def __str__(self, /) -> str:
        return (
            f"'{_escape_single_quoted_literal_characters(self._characters)}'"
        )


class NegativeLookaheadExpression(Expression[LookaheadMatch]):
    __slots__ = ('_expression',)

    def __new__(cls, expression: Expression[MatchLeaf | MatchTree], /) -> Self:
        _validate_expression(expression)
        _validate_progressing_expression(expression)
        self = super().__new__(cls)
        self._expression = expression
        return self

    @override
    def equals_to(
        self, other: Expression[Any], /, *, visited_rule_names: set[str]
    ) -> bool:
        return isinstance(
            other, NegativeLookaheadExpression
        ) and self._expression.equals_to(
            other._expression,  # noqa: SLF001
            visited_rule_names=visited_rule_names,
        )

    @override
    def evaluate(
        self,
        text: str,
        index: int,
        /,
        *,
        cache: dict[str, dict[int, AnyMatch | Mismatch]],
        rule_name: str | None,
    ) -> LookaheadMatch | Mismatch:
        return (
            LookaheadMatch(rule_name)
            if is_mismatch(
                self._expression.evaluate(
                    text, index, cache=cache, rule_name=None
                )
            )
            else Mismatch(rule_name, index)
        )

    @override
    def to_match_classes(self, /) -> Iterable[type[LookaheadMatch]]:
        yield LookaheadMatch

    @override
    def to_nested_str(self, /) -> str:
        return f'({self.__str__()})'

    _expression: Expression[MatchLeaf | MatchTree]

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression!r})'

    @override
    def __str__(self, /) -> str:
        return f'!{self._expression.to_nested_str()}'


class OneOrMoreExpression(Expression[MatchTree]):
    __slots__ = ('_expression',)

    def __new__(cls, expression: Expression[MatchLeaf | MatchTree], /) -> Self:
        _validate_expression(expression)
        _validate_progressing_expression(expression)
        self = super().__new__(cls)
        self._expression = expression
        return self

    @override
    def equals_to(
        self, other: Expression[Any], /, *, visited_rule_names: set[str]
    ) -> bool:
        return isinstance(
            other, OneOrMoreExpression
        ) and self._expression.equals_to(
            other._expression,  # noqa: SLF001
            visited_rule_names=visited_rule_names,
        )

    @override
    def evaluate(
        self,
        text: str,
        index: int,
        /,
        *,
        cache: dict[str, dict[int, AnyMatch | Mismatch]],
        rule_name: str | None,
    ) -> MatchTree | Mismatch:
        children: list[MatchLeaf | MatchTree] = []
        expression = self._expression
        while not is_mismatch(
            match := expression.evaluate(
                text, index, cache=cache, rule_name=None
            )
        ):
            assert isinstance(match, MatchLeaf | MatchTree)
            children.append(match)
            index += match.characters_count
        if len(children) == 0:
            return Mismatch(rule_name, index)
        return MatchTree(rule_name, children=children)

    @override
    def to_match_classes(self, /) -> Iterable[type[MatchTree]]:
        yield MatchTree

    @override
    def to_nested_str(self, /) -> str:
        return f'({self.__str__()})'

    _expression: Expression[MatchLeaf | MatchTree]

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression!r})'

    @override
    def __str__(self, /) -> str:
        return f'{self._expression.to_nested_str()}+'


class OptionalExpression(Expression[AnyMatch]):
    __slots__ = ('_expression',)

    def __new__(cls, expression: Expression[MatchLeaf | MatchTree], /) -> Self:
        _validate_expression(expression)
        _validate_progressing_expression(expression)
        self = super().__new__(cls)
        self._expression = expression
        return self

    @override
    def equals_to(
        self, other: Expression[Any], /, *, visited_rule_names: set[str]
    ) -> bool:
        return isinstance(
            other, OptionalExpression
        ) and self._expression.equals_to(
            other._expression,  # noqa: SLF001
            visited_rule_names=visited_rule_names,
        )

    @override
    def evaluate(
        self,
        text: str,
        index: int,
        /,
        *,
        cache: dict[str, dict[int, AnyMatch | Mismatch]],
        rule_name: str | None,
    ) -> AnyMatch | Mismatch:
        return (
            result
            if not is_mismatch(
                result := self._expression.evaluate(
                    text, index, cache=cache, rule_name=rule_name
                )
            )
            else LookaheadMatch(rule_name)
        )

    @override
    def to_match_classes(self, /) -> Iterable[type[AnyMatch]]:
        yield LookaheadMatch
        yield from self._expression.to_match_classes()

    @override
    def to_nested_str(self, /) -> str:
        return f'({self.__str__()})'

    _expression: Expression[MatchLeaf | MatchTree]

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression!r})'

    @override
    def __str__(self, /) -> str:
        return f'{self._expression.to_nested_str()}?'


class PositiveLookaheadExpression(Expression[LookaheadMatch]):
    __slots__ = ('_expression',)

    def __new__(cls, expression: Expression[MatchLeaf | MatchTree], /) -> Self:
        _validate_expression(expression)
        _validate_progressing_expression(expression)
        self = super().__new__(cls)
        self._expression = expression
        return self

    @override
    def equals_to(
        self, other: Expression[Any], /, *, visited_rule_names: set[str]
    ) -> bool:
        return isinstance(
            other, PositiveLookaheadExpression
        ) and self._expression.equals_to(
            other._expression,  # noqa: SLF001
            visited_rule_names=visited_rule_names,
        )

    @override
    def evaluate(
        self,
        text: str,
        index: int,
        /,
        *,
        cache: dict[str, dict[int, AnyMatch | Mismatch]],
        rule_name: str | None,
    ) -> LookaheadMatch | Mismatch:
        return (
            Mismatch(rule_name, index)
            if is_mismatch(
                self._expression.evaluate(
                    text, index, cache=cache, rule_name=None
                )
            )
            else LookaheadMatch(rule_name)
        )

    @override
    def to_match_classes(self, /) -> Iterable[type[LookaheadMatch]]:
        yield LookaheadMatch

    @override
    def to_nested_str(self, /) -> str:
        return f'({self.__str__()})'

    _expression: Expression[MatchLeaf | MatchTree]

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression!r})'

    @override
    def __str__(self, /) -> str:
        return f'&{self._expression.to_nested_str()}'


class PositiveOrMoreExpression(Expression[MatchTree]):
    MIN_START: ClassVar[int] = 2

    __slots__ = '_expression', '_start'

    def __new__(
        cls, expression: Expression[MatchLeaf | MatchTree], start: int, /
    ) -> Self:
        _validate_repetition_bound(start)
        _validate_expression(expression)
        _validate_progressing_expression(expression)
        if start < cls.MIN_START:
            raise ValueError(
                f'Repetition start should not be less than {cls.MIN_START!r}, '
                f'but got {start!r}.'
            )
        self = super().__new__(cls)
        self._expression, self._start = expression, start
        return self

    @override
    def equals_to(
        self, other: Expression[Any], /, *, visited_rule_names: set[str]
    ) -> bool:
        return (
            isinstance(other, PositiveOrMoreExpression)
            and self._start == other._start
            and self._expression.equals_to(
                other._expression, visited_rule_names=visited_rule_names
            )
        )

    @override
    def evaluate(
        self,
        text: str,
        index: int,
        /,
        *,
        cache: dict[str, dict[int, AnyMatch | Mismatch]],
        rule_name: str | None,
    ) -> MatchTree | Mismatch:
        children: list[MatchLeaf | MatchTree] = []
        expression = self._expression
        start_index = index
        for _ in range(self._start):
            if not is_mismatch(
                match := expression.evaluate(
                    text, index, cache=cache, rule_name=None
                )
            ):
                assert isinstance(match, MatchLeaf | MatchTree)
                children.append(match)
                index += match.characters_count
            else:
                return Mismatch(rule_name, start_index)
        while not is_mismatch(
            match := expression.evaluate(
                text, index, cache=cache, rule_name=None
            )
        ):
            assert isinstance(match, MatchLeaf | MatchTree)
            children.append(match)
            index += match.characters_count
        return MatchTree(rule_name, children=children)

    @override
    def to_match_classes(self, /) -> Iterable[type[MatchTree]]:
        yield MatchTree

    @override
    def to_nested_str(self, /) -> str:
        return f'({self.__str__()})'

    _expression: Expression[MatchLeaf | MatchTree]
    _start: int

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression!r})'

    @override
    def __str__(self, /) -> str:
        return f'{self._expression.to_nested_str()}{{{self._start},}}'


class PositiveRepetitionRangeExpression(Expression[MatchTree]):
    MIN_START: ClassVar[int] = 1

    __slots__ = '_end', '_expression', '_start'

    def __new__(
        cls,
        expression: Expression[MatchLeaf | MatchTree],
        start: int,
        end: int,
        /,
    ) -> Self:
        _validate_repetition_bound(start)
        _validate_repetition_bound(end)
        _validate_expression(expression)
        _validate_progressing_expression(expression)
        if start < cls.MIN_START:
            raise ValueError(
                'Repetition range start should not be less '
                f'than {cls.MIN_START!r}, '
                f'but got {start!r}.'
            )
        if start >= end:
            raise ValueError(
                'Repetition range start should be less than end, '
                f'but got {start!r} >= {end!r}.'
            )
        self = super().__new__(cls)
        self._expression, self._end, self._start = expression, end, start
        return self

    @override
    def equals_to(
        self, other: Expression[Any], /, *, visited_rule_names: set[str]
    ) -> bool:
        return (
            isinstance(other, PositiveRepetitionRangeExpression)
            and self._start == other._start
            and self._end == other._end
            and self._expression.equals_to(
                other._expression, visited_rule_names=visited_rule_names
            )
        )

    @override
    def evaluate(
        self,
        text: str,
        index: int,
        /,
        *,
        cache: dict[str, dict[int, AnyMatch | Mismatch]],
        rule_name: str | None,
    ) -> MatchTree | Mismatch:
        children: list[MatchLeaf | MatchTree] = []
        expression = self._expression
        start_index = index
        for _ in range(self._start):
            if not is_mismatch(
                match := expression.evaluate(
                    text, index, cache=cache, rule_name=None
                )
            ):
                assert isinstance(match, MatchLeaf | MatchTree)
                children.append(match)
                index += match.characters_count
            else:
                return Mismatch(rule_name, start_index)
        for _ in range(self._start, self._end):
            if not is_mismatch(
                match := expression.evaluate(
                    text, index, cache=cache, rule_name=None
                )
            ):
                assert isinstance(match, MatchLeaf | MatchTree)
                children.append(match)
                index += match.characters_count
            else:
                break
        return MatchTree(rule_name, children=children)

    @override
    def to_match_classes(self, /) -> Iterable[type[MatchTree]]:
        yield MatchTree

    @override
    def to_nested_str(self, /) -> str:
        return f'({self.__str__()})'

    _expression: Expression[MatchLeaf | MatchTree]
    _end: int
    _start: int

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression!r})'

    @override
    def __str__(self, /) -> str:
        return (
            f'{self._expression.to_nested_str()}{{{self._start},{self._end}}}'
        )


class PrioritizedChoiceExpression(Expression[MatchT_co]):
    __slots__ = ('_variants',)

    def __new__(cls, variants: Sequence[Expression[MatchT_co]], /) -> Self:
        assert len(variants) > 1, variants
        self = super().__new__(cls)
        self._variants = variants
        return self

    @property
    def variants(self, /) -> Sequence[Expression[MatchT_co]]:
        return self._variants

    @override
    def equals_to(
        self, other: Expression[Any], /, *, visited_rule_names: set[str]
    ) -> bool:
        return (
            isinstance(other, PrioritizedChoiceExpression)
            and len(self._variants) == len(other._variants)  # noqa: SLF001
            and all(
                variant.equals_to(
                    other_variant, visited_rule_names=visited_rule_names
                )
                for variant, other_variant in zip(
                    self._variants,
                    other._variants,  # noqa: SLF001
                    strict=True,
                )
            )
        )

    @override
    def evaluate(
        self,
        text: str,
        index: int,
        /,
        *,
        cache: dict[str, dict[int, AnyMatch | Mismatch]],
        rule_name: str | None,
    ) -> MatchT_co | Mismatch:
        return next(
            (
                variant_match
                for variant in self._variants
                if not is_mismatch(
                    variant_match := variant.evaluate(
                        text, index, cache=cache, rule_name=rule_name
                    )
                )
            ),
            Mismatch(rule_name, index),
        )

    @override
    def to_match_classes(self, /) -> Iterable[type[MatchT_co]]:
        for variant in self._variants:
            yield from variant.to_match_classes()

    @override
    def to_nested_str(self, /) -> str:
        return f'({self.__str__()})'

    _variants: Sequence[Expression[MatchT_co]]

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self.variants!r})'

    @override
    def __str__(self, /) -> str:
        return ' / '.join(
            map(
                methodcaller(Expression.to_nested_str.__name__), self._variants
            )
        )


@final
class RuleReference(Expression[MatchT_co]):
    __slots__ = '_match_classes', '_name', '_referent_name', '_rules'

    def __new__(
        cls,
        name: str,
        referent_name: str,
        /,
        *,
        match_classes: Sequence[type[MatchT_co]],
        rules: Mapping[str, Rule[MatchT_co]],
    ) -> Self:
        assert len(name) > 0, name
        self = super().__new__(cls)
        self._match_classes, self._name, self._referent_name, self._rules = (
            match_classes,
            name,
            referent_name,
            rules,
        )
        return self

    @override
    def equals_to(
        self, other: Expression[Any], /, *, visited_rule_names: set[str]
    ) -> bool:
        if not (
            isinstance(other, RuleReference)
            and (
                self._name == other._name  # noqa: SLF001
                and self._referent_name == other._referent_name  # noqa: SLF001
            )
        ):
            return False
        if self._name in visited_rule_names:
            return True
        visited_rule_names.add(self._name)
        result = self._get_rule().expression.equals_to(
            other._get_rule().expression,  # noqa: SLF001
            visited_rule_names=visited_rule_names,
        )
        visited_rule_names.remove(self._name)
        return result

    @override
    def evaluate(
        self,
        text: str,
        index: int,
        /,
        *,
        cache: dict[str, dict[int, AnyMatch | Mismatch]],
        rule_name: str | None,
    ) -> MatchT_co | Mismatch:
        return self._get_rule().parse(
            text, index, cache=cache, rule_name=self._name
        )

    @override
    def to_match_classes(self) -> Iterable[type[MatchT_co]]:
        return iter(self._match_classes)

    @override
    def to_nested_str(self, /) -> str:
        return self.__str__()

    def _get_rule(self, /) -> Rule[MatchT_co]:
        return self._rules[self._referent_name]

    _match_classes: Sequence[type[MatchT_co]]
    _name: str
    _referent_name: str
    _rules: Mapping[str, Rule[MatchT_co]]

    @override
    def __repr__(self, /) -> str:
        return (
            f'{type(self).__qualname__}'
            '('
            f'{self._name!r}, {self._referent_name!r}, rules={self._rules!r}'
            ')'
        )

    @override
    def __str__(self, /) -> str:
        return self._name


class SequenceExpression(Expression[MatchTree]):
    __slots__ = ('_elements',)

    def __new__(cls, elements: Sequence[Expression[AnyMatch]], /) -> Self:
        if not any(
            _is_progressing_expression(element) for element in elements
        ):
            raise ValueError(elements)
        assert len(elements) > 1, elements
        self = super().__new__(cls)
        self._elements = elements
        return self

    @override
    def equals_to(
        self, other: Expression[Any], /, *, visited_rule_names: set[str]
    ) -> bool:
        return (
            isinstance(other, SequenceExpression)
            and len(self._elements) == len(other._elements)  # noqa: SLF001
            and all(
                element.equals_to(
                    other_element, visited_rule_names=visited_rule_names
                )
                for element, other_element in zip(
                    self._elements,
                    other._elements,  # noqa: SLF001
                    strict=True,
                )
            )
        )

    @override
    def evaluate(
        self,
        text: str,
        index: int,
        /,
        *,
        cache: dict[str, dict[int, AnyMatch | Mismatch]],
        rule_name: str | None,
    ) -> MatchTree | Mismatch:
        non_lookahead_matches: list[MatchLeaf | MatchTree] = []
        for element in self._elements:
            if not is_mismatch(
                element_match := element.evaluate(
                    text, index, cache=cache, rule_name=None
                )
            ):
                if isinstance(element_match, LookaheadMatch):
                    continue
                assert isinstance(element_match, MatchLeaf | MatchTree), (
                    element_match
                )
                non_lookahead_matches.append(element_match)
                index += element_match.characters_count
            else:
                return Mismatch(rule_name, index)
        assert len(non_lookahead_matches) > 0, non_lookahead_matches
        return MatchTree(rule_name, children=non_lookahead_matches)

    @override
    def to_match_classes(self, /) -> Iterable[type[MatchTree]]:
        yield MatchTree

    @override
    def to_nested_str(self, /) -> str:
        return f'({self.__str__()})'

    _elements: Sequence[Expression[AnyMatch]]

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._elements!r})'

    @override
    def __str__(self, /) -> str:
        return ' '.join(
            map(
                methodcaller(Expression.to_nested_str.__name__), self._elements
            )
        )


class ZeroOrMoreExpression(Expression[LookaheadMatch | MatchTree]):
    __slots__ = ('_expression',)

    def __new__(cls, expression: Expression[MatchLeaf | MatchTree], /) -> Self:
        _validate_expression(expression)
        _validate_progressing_expression(expression)
        self = super().__new__(cls)
        self._expression = expression
        return self

    @override
    def equals_to(
        self, other: Expression[Any], /, *, visited_rule_names: set[str]
    ) -> bool:
        return isinstance(
            other, ZeroOrMoreExpression
        ) and self._expression.equals_to(
            other._expression,  # noqa: SLF001
            visited_rule_names=visited_rule_names,
        )

    @override
    def evaluate(
        self,
        text: str,
        index: int,
        /,
        *,
        cache: dict[str, dict[int, AnyMatch | Mismatch]],
        rule_name: str | None,
    ) -> LookaheadMatch | MatchTree:
        children: list[MatchLeaf | MatchTree] = []
        expression = self._expression
        while not is_mismatch(
            match := expression.evaluate(
                text, index, cache=cache, rule_name=None
            )
        ):
            assert isinstance(match, MatchLeaf | MatchTree)
            children.append(match)
            index += match.characters_count
        if len(children) == 0:
            return LookaheadMatch(rule_name)
        return MatchTree(rule_name, children=children)

    @override
    def to_match_classes(
        self, /
    ) -> Iterable[type[LookaheadMatch | MatchTree]]:
        yield LookaheadMatch
        yield MatchTree

    @override
    def to_nested_str(self, /) -> str:
        return f'({self.__str__()})'

    _expression: Expression[MatchLeaf | MatchTree]

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression!r})'

    @override
    def __str__(self, /) -> str:
        return f'{self._expression.to_nested_str()}*'


class ZeroRepetitionRangeExpression(Expression[LookaheadMatch | MatchTree]):
    MIN_END: ClassVar[int] = 2

    __slots__ = '_end', '_expression'

    def __new__(
        cls, expression: Expression[MatchLeaf | MatchTree], end: int, /
    ) -> Self:
        _validate_repetition_bound(end)
        _validate_expression(expression)
        _validate_progressing_expression(expression)
        if end < cls.MIN_END:
            raise ValueError(
                'Repetition range end '
                f'should not be less than {cls.MIN_END!r}, '
                f'but got {end!r}.'
            )
        self = super().__new__(cls)
        self._end, self._expression = end, expression
        return self

    @override
    def equals_to(
        self, other: Expression[Any], /, *, visited_rule_names: set[str]
    ) -> bool:
        return (
            isinstance(other, ZeroRepetitionRangeExpression)
            and self._end == other._end
            and self._expression.equals_to(
                other._expression, visited_rule_names=visited_rule_names
            )
        )

    @override
    def evaluate(
        self,
        text: str,
        index: int,
        /,
        *,
        cache: dict[str, dict[int, AnyMatch | Mismatch]],
        rule_name: str | None,
    ) -> LookaheadMatch | MatchTree | Mismatch:
        children: list[MatchLeaf | MatchTree] = []
        expression = self._expression
        for _ in range(self._end):
            if not is_mismatch(
                match := expression.evaluate(
                    text, index, cache=cache, rule_name=None
                )
            ):
                assert isinstance(match, MatchLeaf | MatchTree)
                children.append(match)
                index += match.characters_count
            else:
                break
        return (
            LookaheadMatch(rule_name)
            if len(children) == 0
            else MatchTree(rule_name, children=children)
        )

    @override
    def to_match_classes(
        self, /
    ) -> Iterable[type[LookaheadMatch | MatchTree]]:
        yield LookaheadMatch
        yield MatchTree

    @override
    def to_nested_str(self, /) -> str:
        return f'({self.__str__()})'

    _end: int
    _expression: Expression[MatchLeaf | MatchTree]

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression!r})'

    @override
    def __str__(self, /) -> str:
        return f'{self._expression.to_nested_str()}{{,{self._end}}}'


def _escape_double_quoted_literal_characters(
    value: str,
    /,
    *,
    translation_table: Mapping[int, str] = MappingProxyType(
        {
            **{
                ord(character): '\\' + character  # type: ignore[name-defined]
                for character in DOUBLE_QUOTED_LITERAL_SPECIAL_CHARACTERS
            },
            **COMMON_SPECIAL_CHARACTERS_TRANSLATION_TABLE,
        }
    ),
) -> str:
    assert isinstance(value, str), value
    assert len(value) > 0, value
    return value.translate(translation_table)


def _escape_single_quoted_literal_characters(
    value: str,
    /,
    *,
    translation_table: Mapping[int, str] = MappingProxyType(
        {
            **{
                ord(character): '\\' + character  # type: ignore[name-defined]
                for character in SINGLE_QUOTED_LITERAL_SPECIAL_CHARACTERS
            },
            **COMMON_SPECIAL_CHARACTERS_TRANSLATION_TABLE,
        }
    ),
) -> str:
    assert isinstance(value, str), value
    assert len(value) > 0, value
    return value.translate(translation_table)


def _is_progressing_expression(
    value: Expression[Any], /
) -> TypeIs[Expression[MatchLeaf | MatchTree]]:
    return not any(
        issubclass(match_cls, LookaheadMatch)
        for match_cls in value.to_match_classes()
    )


def _validate_expression(value: Any, /) -> None:
    if not isinstance(value, Expression):
        raise TypeError(type(value))


def _validate_progressing_expression(value: Expression[Any], /) -> None:
    if not _is_progressing_expression(value):
        raise ValueError(value)


def _validate_repetition_bound(value: Any, /) -> None:
    if not isinstance(value, int):
        raise TypeError(type(value))
