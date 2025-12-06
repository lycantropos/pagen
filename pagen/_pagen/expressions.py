from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping, Sequence
from enum import IntEnum, auto, unique
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
from .mismatch import (
    AnyMismatch,
    MismatchLeaf,
    MismatchT_co,
    MismatchTree,
    NoMismatch,
    is_mismatch,
)

if TYPE_CHECKING:
    from .rule import Rule


@unique
class ExpressionPrecedence(IntEnum):
    PRIORITIZED_CHOICE = auto()
    SEQUENCE = auto()
    REPETITION = auto()
    LOOKAHEAD = auto()
    TERM = auto()


class Expression(ABC, Generic[MatchT_co, MismatchT_co]):
    __slots__ = ()

    @classmethod
    @abstractmethod
    def precedence(cls, /) -> int:
        raise NotImplementedError

    @abstractmethod
    def equals_to(
        self, other: Expression[Any, Any], /, *, visited_rule_names: set[str]
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def evaluate(
        self,
        text: str,
        index: int,
        /,
        *,
        cache: dict[str, dict[int, AnyMatch | AnyMismatch]],
        rule_name: str | None,
    ) -> MatchT_co | MismatchT_co:
        raise NotImplementedError

    def is_valid_match(self, value: Any, /) -> TypeGuard[MatchT_co]:
        return any(
            isinstance(value, match_cls)
            for match_cls in self.to_match_classes()
        )

    def is_valid_mismatch(self, value: Any, /) -> TypeGuard[MismatchT_co]:
        return any(
            isinstance(value, mismatch_cls)
            for mismatch_cls in self.to_mismatch_classes()
        )

    @abstractmethod
    def to_match_classes(self, /) -> Iterable[type[MatchT_co]]:
        raise NotImplementedError

    @abstractmethod
    def to_mismatch_classes(self, /) -> Iterable[type[MismatchT_co]]:
        raise NotImplementedError

    @abstractmethod
    def to_seed_mismatch(self, rule_name: str | None, /) -> MismatchT_co:
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
    def __repr__(self, /) -> str:
        raise NotImplementedError

    @abstractmethod
    def __str__(self, /) -> str:
        raise NotImplementedError


@final
class AnyCharacterExpression(Expression[MatchLeaf, MismatchLeaf]):
    @classmethod
    @override
    def precedence(cls, /) -> int:
        return ExpressionPrecedence.TERM

    @override
    def equals_to(
        self, other: Expression[Any, Any], /, *, visited_rule_names: set[str]
    ) -> bool:
        return isinstance(other, AnyCharacterExpression)

    @override
    def evaluate(
        self,
        text: str,
        index: int,
        /,
        *,
        cache: dict[str, dict[int, AnyMatch | AnyMismatch]],
        rule_name: str | None,
    ) -> MatchLeaf | MismatchLeaf:
        return (
            MatchLeaf(rule_name, characters=text[index])
            if index < len(text)
            else MismatchLeaf(rule_name, characters='')
        )

    @override
    def to_match_classes(self, /) -> Iterable[type[MatchLeaf]]:
        yield MatchLeaf

    @override
    def to_mismatch_classes(self, /) -> Iterable[type[MismatchLeaf]]:
        yield MismatchLeaf

    @override
    def to_seed_mismatch(self, rule_name: str | None, /) -> MismatchLeaf:
        return MismatchLeaf(rule_name, characters='')

    __slots__ = ()

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {AnyCharacterExpression.__qualname__!r} '
            'is not an acceptable base type'
        )

    @override
    def __str__(self, /) -> str:
        return '.'

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}()'


@final
class CharacterClassExpression(Expression[MatchLeaf, MismatchLeaf]):
    MIN_ELEMENTS_COUNT: ClassVar[int] = 1

    @classmethod
    @override
    def precedence(cls, /) -> int:
        return ExpressionPrecedence.TERM

    @property
    def elements(self, /) -> Sequence[CharacterRange | CharacterSet]:
        return self._elements

    @override
    def equals_to(
        self, other: Expression[Any, Any], /, *, visited_rule_names: set[str]
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
        cache: dict[str, dict[int, AnyMatch | AnyMismatch]],
        rule_name: str | None,
    ) -> MatchLeaf | MismatchLeaf:
        if index >= len(text):
            return MismatchLeaf(rule_name, characters='')
        character = text[index]
        return (
            MatchLeaf(rule_name, characters=character)
            if any(character in element for element in self._elements)
            else MismatchLeaf(rule_name, characters=character)
        )

    @override
    def to_match_classes(self, /) -> Iterable[type[MatchLeaf]]:
        yield MatchLeaf

    @override
    def to_mismatch_classes(self, /) -> Iterable[type[MismatchLeaf]]:
        yield MismatchLeaf

    @override
    def to_seed_mismatch(self, rule_name: str | None, /) -> MismatchLeaf:
        return MismatchLeaf(rule_name, characters='')

    __slots__ = ('_elements',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {CharacterClassExpression.__qualname__!r} '
            'is not an acceptable base type'
        )

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

    _elements: Sequence[CharacterRange | CharacterSet]

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._elements!r})'

    @override
    def __str__(self, /) -> str:
        return f'[{"".join(map(str, self._elements))}]'


@final
class ComplementedCharacterClassExpression(
    Expression[MatchLeaf, MismatchLeaf]
):
    MIN_ELEMENTS_COUNT: ClassVar[int] = 1

    @classmethod
    @override
    def precedence(cls, /) -> int:
        return ExpressionPrecedence.TERM

    @property
    def elements(self, /) -> Sequence[CharacterRange | CharacterSet]:
        return self._elements

    @override
    def equals_to(
        self, other: Expression[Any, Any], /, *, visited_rule_names: set[str]
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
        cache: dict[str, dict[int, AnyMatch | AnyMismatch]],
        rule_name: str | None,
    ) -> MatchLeaf | MismatchLeaf:
        if index >= len(text):
            return MismatchLeaf(rule_name, characters='')
        character = text[index]
        return (
            MatchLeaf(rule_name, characters=character)
            if all(character not in element for element in self._elements)
            else MismatchLeaf(rule_name, characters=character)
        )

    @override
    def to_match_classes(self, /) -> Iterable[type[MatchLeaf]]:
        yield MatchLeaf

    @override
    def to_mismatch_classes(self, /) -> Iterable[type[MismatchLeaf]]:
        yield MismatchLeaf

    @override
    def to_seed_mismatch(self, rule_name: str | None, /) -> MismatchLeaf:
        return MismatchLeaf(rule_name, characters='')

    __slots__ = ('_elements',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {ComplementedCharacterClassExpression.__qualname__!r} '
            'is not an acceptable base type'
        )

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

    _elements: Sequence[CharacterRange | CharacterSet]

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._elements!r})'

    @override
    def __str__(self, /) -> str:
        return f'[^{"".join(map(str, self._elements))}]'


@final
class ExactRepetitionExpression(Expression[MatchTree, MismatchTree]):
    MIN_COUNT: ClassVar[int] = 2

    @classmethod
    @override
    def precedence(cls, /) -> int:
        return ExpressionPrecedence.REPETITION

    @property
    def count(self, /) -> int:
        return self._count

    @property
    def expression(self, /) -> Expression[MatchLeaf | MatchTree, AnyMismatch]:
        return self._expression

    @override
    def equals_to(
        self, other: Expression[Any, Any], /, *, visited_rule_names: set[str]
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
        cache: dict[str, dict[int, AnyMatch | AnyMismatch]],
        rule_name: str | None,
    ) -> MatchTree | MismatchTree:
        children: list[MatchLeaf | MatchTree] = []
        expression = self._expression
        for _ in range(self._count):
            match = expression.evaluate(
                text, index, cache=cache, rule_name=None
            )
            if is_mismatch(match):
                return MismatchTree(rule_name, children=[*children, match])
            else:
                assert isinstance(match, MatchLeaf | MatchTree)
                children.append(match)
                index += match.characters_count
        return MatchTree(rule_name, children=children)

    @override
    def to_match_classes(self, /) -> Iterable[type[MatchTree]]:
        yield MatchTree

    @override
    def to_mismatch_classes(self, /) -> Iterable[type[MismatchTree]]:
        yield MismatchTree

    @override
    def to_seed_mismatch(self, rule_name: str | None, /) -> MismatchTree:
        return MismatchTree(
            rule_name, children=[MismatchLeaf(None, characters='')]
        )

    __slots__ = '_count', '_expression'

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {ExactRepetitionExpression.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls,
        expression: Expression[MatchLeaf | MatchTree, AnyMismatch],
        count: int,
        /,
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

    _count: int
    _expression: Expression[MatchLeaf | MatchTree, AnyMismatch]

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression!r})'

    @override
    def __str__(self, /) -> str:
        expression_str = _to_nested_expression_str(
            self._expression, parent_precedence=self.precedence()
        )
        return f'{expression_str}{{{self._count}}}'


class LiteralExpression(Expression[MatchLeaf, MismatchLeaf]):
    MIN_CHARACTERS_COUNT: ClassVar[int] = 1

    @classmethod
    @override
    def precedence(cls, /) -> int:
        return ExpressionPrecedence.TERM

    @property
    @abstractmethod
    def characters(self, /) -> str:
        pass

    @override
    def equals_to(
        self, other: Expression[Any, Any], /, *, visited_rule_names: set[str]
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
        cache: dict[str, dict[int, AnyMatch | AnyMismatch]],
        rule_name: str | None,
    ) -> MatchLeaf | MismatchLeaf:
        return (
            MismatchLeaf(rule_name, characters=characters)
            if (
                (characters := text[index : index + len(self.characters)])
                != self.characters
            )
            else MatchLeaf(rule_name, characters=self.characters)
        )

    @override
    def to_match_classes(self, /) -> Iterable[type[MatchLeaf]]:
        yield MatchLeaf

    @override
    def to_mismatch_classes(self, /) -> Iterable[type[MismatchLeaf]]:
        yield MismatchLeaf

    @override
    def to_seed_mismatch(self, rule_name: str | None, /) -> MismatchLeaf:
        return MismatchLeaf(rule_name, characters='')

    __slots__ = ()

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


@final
class DoubleQuotedLiteralExpression(LiteralExpression):
    @property
    @override
    def characters(self, /) -> str:
        return self._characters

    __slots__ = ('_characters',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {DoubleQuotedLiteralExpression.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(cls, characters: str, /) -> Self:
        cls._validate_characters(characters)
        self = super().__new__(cls)
        self._characters = characters
        return self

    _characters: str

    @override
    def __str__(self, /) -> str:
        return (
            f'"{_escape_double_quoted_literal_characters(self._characters)}"'
        )


@final
class SingleQuotedLiteralExpression(LiteralExpression):
    @property
    @override
    def characters(self, /) -> str:
        return self._characters

    __slots__ = ('_characters',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {SingleQuotedLiteralExpression.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(cls, characters: str, /) -> Self:
        cls._validate_characters(characters)
        self = super().__new__(cls)
        self._characters = characters
        return self

    _characters: str

    @override
    def __str__(self, /) -> str:
        return (
            f"'{_escape_single_quoted_literal_characters(self._characters)}'"
        )


@final
class NegativeLookaheadExpression(Expression[LookaheadMatch, MismatchTree]):
    @classmethod
    @override
    def precedence(cls, /) -> int:
        return ExpressionPrecedence.LOOKAHEAD

    @property
    def expression(self, /) -> Expression[MatchLeaf | MatchTree, AnyMismatch]:
        return self._expression

    @override
    def equals_to(
        self, other: Expression[Any, Any], /, *, visited_rule_names: set[str]
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
        cache: dict[str, dict[int, AnyMatch | AnyMismatch]],
        rule_name: str | None,
    ) -> LookaheadMatch | MismatchTree:
        return (
            MismatchTree(rule_name, children=[match])
            if not is_mismatch(
                match := self._expression.evaluate(
                    text, index, cache=cache, rule_name=None
                )
            )
            else LookaheadMatch(rule_name)
        )

    @override
    def to_match_classes(self, /) -> Iterable[type[LookaheadMatch]]:
        yield LookaheadMatch

    @override
    def to_mismatch_classes(self, /) -> Iterable[type[MismatchTree]]:
        yield MismatchTree

    @override
    def to_seed_mismatch(self, rule_name: str | None, /) -> MismatchTree:
        return MismatchTree(
            rule_name, children=[MismatchLeaf(None, characters='')]
        )

    __slots__ = ('_expression',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {NegativeLookaheadExpression.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls, expression: Expression[MatchLeaf | MatchTree, AnyMismatch], /
    ) -> Self:
        _validate_expression(expression)
        _validate_progressing_expression(expression)
        self = super().__new__(cls)
        self._expression = expression
        return self

    _expression: Expression[MatchLeaf | MatchTree, AnyMismatch]

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression!r})'

    @override
    def __str__(self, /) -> str:
        expression_str = _to_nested_expression_str(
            self._expression, parent_precedence=self.precedence()
        )
        return f'!{expression_str}'


@final
class OneOrMoreExpression(Expression[MatchTree, MismatchTree]):
    @classmethod
    @override
    def precedence(cls, /) -> int:
        return ExpressionPrecedence.REPETITION

    @property
    def expression(self, /) -> Expression[MatchLeaf | MatchTree, AnyMismatch]:
        return self._expression

    @override
    def equals_to(
        self, other: Expression[Any, Any], /, *, visited_rule_names: set[str]
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
        cache: dict[str, dict[int, AnyMatch | AnyMismatch]],
        rule_name: str | None,
    ) -> MatchTree | MismatchTree:
        expression = self._expression
        first_match = expression.evaluate(
            text, index, cache=cache, rule_name=None
        )
        if is_mismatch(first_match):
            return MismatchTree(rule_name, children=[first_match])
        else:
            children: list[MatchLeaf | MatchTree] = [first_match]
            index += first_match.characters_count
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

    def to_mismatch_classes(self, /) -> Iterable[type[MismatchTree]]:
        yield MismatchTree

    @override
    def to_seed_mismatch(self, rule_name: str | None, /) -> MismatchTree:
        return MismatchTree(
            rule_name, children=[MismatchLeaf(None, characters='')]
        )

    __slots__ = ('_expression',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {OneOrMoreExpression.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls, expression: Expression[MatchLeaf | MatchTree, AnyMismatch], /
    ) -> Self:
        _validate_expression(expression)
        _validate_progressing_expression(expression)
        self = super().__new__(cls)
        self._expression = expression
        return self

    _expression: Expression[MatchLeaf | MatchTree, AnyMismatch]

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression!r})'

    @override
    def __str__(self, /) -> str:
        expression_str = _to_nested_expression_str(
            self._expression, parent_precedence=self.precedence()
        )
        return f'{expression_str}+'


@final
class OptionalExpression(Expression[AnyMatch, NoMismatch]):
    @classmethod
    @override
    def precedence(cls, /) -> int:
        return ExpressionPrecedence.REPETITION

    @property
    def expression(self, /) -> Expression[MatchLeaf | MatchTree, AnyMismatch]:
        return self._expression

    @override
    def equals_to(
        self, other: Expression[Any, Any], /, *, visited_rule_names: set[str]
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
        cache: dict[str, dict[int, AnyMatch | AnyMismatch]],
        rule_name: str | None,
    ) -> AnyMatch | NoMismatch:
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
    def to_mismatch_classes(self, /) -> Iterable[type[NoMismatch]]:
        yield from ()

    @override
    def to_seed_mismatch(self, rule_name: str | None, /) -> NoMismatch:
        raise ValueError(self)

    __slots__ = ('_expression',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {OptionalExpression.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls, expression: Expression[MatchLeaf | MatchTree, AnyMismatch], /
    ) -> Self:
        _validate_expression(expression)
        _validate_progressing_expression(expression)
        self = super().__new__(cls)
        self._expression = expression
        return self

    _expression: Expression[MatchLeaf | MatchTree, AnyMismatch]

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression!r})'

    @override
    def __str__(self, /) -> str:
        expression_str = _to_nested_expression_str(
            self._expression, parent_precedence=self.precedence()
        )
        return f'{expression_str}?'


@final
class PositiveLookaheadExpression(Expression[LookaheadMatch, MismatchTree]):
    @classmethod
    @override
    def precedence(cls, /) -> int:
        return ExpressionPrecedence.LOOKAHEAD

    @property
    def expression(self, /) -> Expression[MatchLeaf | MatchTree, AnyMismatch]:
        return self._expression

    @override
    def equals_to(
        self, other: Expression[Any, Any], /, *, visited_rule_names: set[str]
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
        cache: dict[str, dict[int, AnyMatch | AnyMismatch]],
        rule_name: str | None,
    ) -> LookaheadMatch | MismatchTree:
        return (
            MismatchTree(rule_name, children=[match])
            if is_mismatch(
                match := self._expression.evaluate(
                    text, index, cache=cache, rule_name=None
                )
            )
            else LookaheadMatch(rule_name)
        )

    @override
    def to_match_classes(self, /) -> Iterable[type[LookaheadMatch]]:
        yield LookaheadMatch

    @override
    def to_mismatch_classes(self, /) -> Iterable[type[MismatchTree]]:
        yield MismatchTree

    @override
    def to_seed_mismatch(self, rule_name: str | None, /) -> MismatchTree:
        return MismatchTree(
            rule_name, children=[MismatchLeaf(None, characters='')]
        )

    __slots__ = ('_expression',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {PositiveLookaheadExpression.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls, expression: Expression[MatchLeaf | MatchTree, AnyMismatch], /
    ) -> Self:
        _validate_expression(expression)
        _validate_progressing_expression(expression)
        self = super().__new__(cls)
        self._expression = expression
        return self

    _expression: Expression[MatchLeaf | MatchTree, AnyMismatch]

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression!r})'

    @override
    def __str__(self, /) -> str:
        expression_str = _to_nested_expression_str(
            self._expression, parent_precedence=self.precedence()
        )
        return f'&{expression_str}'


@final
class PositiveOrMoreExpression(Expression[MatchTree, MismatchTree]):
    MIN_START: ClassVar[int] = 2

    @classmethod
    @override
    def precedence(cls, /) -> int:
        return ExpressionPrecedence.REPETITION

    @property
    def expression(self, /) -> Expression[MatchLeaf | MatchTree, AnyMismatch]:
        return self._expression

    @property
    def start(self, /) -> int:
        return self._start

    @override
    def equals_to(
        self, other: Expression[Any, Any], /, *, visited_rule_names: set[str]
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
        cache: dict[str, dict[int, AnyMatch | AnyMismatch]],
        rule_name: str | None,
    ) -> MatchTree | MismatchTree:
        children: list[MatchLeaf | MatchTree] = []
        expression = self._expression
        for _ in range(self._start):
            match = expression.evaluate(
                text, index, cache=cache, rule_name=None
            )
            if is_mismatch(match):
                return MismatchTree(rule_name, children=[*children, match])
            else:
                assert isinstance(match, MatchLeaf | MatchTree)
                children.append(match)
                index += match.characters_count
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
    def to_mismatch_classes(self, /) -> Iterable[type[MismatchTree]]:
        yield MismatchTree

    @override
    def to_seed_mismatch(self, rule_name: str | None, /) -> MismatchTree:
        return MismatchTree(
            rule_name, children=[MismatchLeaf(None, characters='')]
        )

    __slots__ = '_expression', '_start'

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {PositiveOrMoreExpression.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls,
        expression: Expression[MatchLeaf | MatchTree, AnyMismatch],
        start: int,
        /,
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

    _expression: Expression[MatchLeaf | MatchTree, AnyMismatch]
    _start: int

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression!r})'

    @override
    def __str__(self, /) -> str:
        expression_str = _to_nested_expression_str(
            self._expression, parent_precedence=self.precedence()
        )
        return f'{expression_str}{{{self._start},}}'


@final
class PositiveRepetitionRangeExpression(Expression[MatchTree, MismatchTree]):
    MIN_START: ClassVar[int] = 1

    @classmethod
    @override
    def precedence(cls, /) -> int:
        return ExpressionPrecedence.REPETITION

    @property
    def end(self, /) -> int:
        return self._end

    @property
    def expression(self, /) -> Expression[MatchLeaf | MatchTree, AnyMismatch]:
        return self._expression

    @property
    def start(self, /) -> int:
        return self._start

    @override
    def equals_to(
        self, other: Expression[Any, Any], /, *, visited_rule_names: set[str]
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
        cache: dict[str, dict[int, AnyMatch | AnyMismatch]],
        rule_name: str | None,
    ) -> MatchTree | MismatchTree:
        children: list[MatchLeaf | MatchTree] = []
        expression = self._expression
        for _ in range(self._start):
            match = expression.evaluate(
                text, index, cache=cache, rule_name=None
            )
            if is_mismatch(match):
                return MismatchTree(rule_name, children=[*children, match])
            else:
                assert isinstance(match, MatchLeaf | MatchTree)
                children.append(match)
                index += match.characters_count
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
    def to_mismatch_classes(self, /) -> Iterable[type[MismatchTree]]:
        yield MismatchTree

    @override
    def to_seed_mismatch(self, rule_name: str | None, /) -> MismatchTree:
        return MismatchTree(
            rule_name, children=[MismatchLeaf(None, characters='')]
        )

    __slots__ = '_end', '_expression', '_start'

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {PositiveRepetitionRangeExpression.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls,
        expression: Expression[MatchLeaf | MatchTree, AnyMismatch],
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

    _expression: Expression[MatchLeaf | MatchTree, AnyMismatch]
    _end: int
    _start: int

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression!r})'

    @override
    def __str__(self, /) -> str:
        expression_str = _to_nested_expression_str(
            self._expression, parent_precedence=self.precedence()
        )
        return f'{expression_str}{{{self._start},{self._end}}}'


@final
class PrioritizedChoiceExpression(Expression[MatchT_co, MismatchTree]):
    @classmethod
    @override
    def precedence(cls, /) -> int:
        return ExpressionPrecedence.PRIORITIZED_CHOICE

    @property
    def variants(self, /) -> Sequence[Expression[MatchT_co, AnyMismatch]]:
        return self._variants

    @override
    def equals_to(
        self, other: Expression[Any, Any], /, *, visited_rule_names: set[str]
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
        cache: dict[str, dict[int, AnyMatch | AnyMismatch]],
        rule_name: str | None,
    ) -> MatchT_co | MismatchTree:
        variant_mismatches = []
        for variant in self._variants:
            variant_match = variant.evaluate(
                text, index, cache=cache, rule_name=rule_name
            )
            if is_mismatch(variant_match):
                variant_mismatches.append(variant_match)
            else:
                return variant_match
        return MismatchTree(rule_name, children=variant_mismatches)

    @override
    def to_match_classes(self, /) -> Iterable[type[MatchT_co]]:
        for variant in self._variants:
            yield from variant.to_match_classes()

    @override
    def to_mismatch_classes(self, /) -> Iterable[type[MismatchTree]]:
        yield MismatchTree

    @override
    def to_seed_mismatch(self, rule_name: str | None, /) -> MismatchTree:
        return MismatchTree(
            rule_name, children=[MismatchLeaf(None, characters='')]
        )

    __slots__ = ('_variants',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {PrioritizedChoiceExpression.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls, variants: Sequence[Expression[MatchT_co, AnyMismatch]], /
    ) -> Self:
        assert len(variants) > 1, variants
        self = super().__new__(cls)
        self._variants = variants
        return self

    _variants: Sequence[Expression[MatchT_co, AnyMismatch]]

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._variants!r})'

    @override
    def __str__(self, /) -> str:
        parent_precedence = self.precedence()
        return ' / '.join(
            _to_nested_expression_str(
                variant, parent_precedence=parent_precedence
            )
            for variant in self._variants
        )


@final
class RuleReference(Expression[MatchT_co, MismatchT_co]):
    @classmethod
    @override
    def precedence(cls, /) -> int:
        return ExpressionPrecedence.TERM

    @property
    def name(self, /) -> str:
        return self._name

    @override
    def equals_to(
        self, other: Expression[Any, Any], /, *, visited_rule_names: set[str]
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
        result = self.resolve().expression.equals_to(
            other.resolve().expression, visited_rule_names=visited_rule_names
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
        cache: dict[str, dict[int, AnyMatch | AnyMismatch]],
        rule_name: str | None,
    ) -> MatchT_co | MismatchT_co:
        return self.resolve().parse(
            text, index, cache=cache, rule_name=self._name
        )

    def resolve(self, /) -> Rule[MatchT_co, MismatchT_co]:
        return self._rules[self._referent_name]

    @override
    def to_match_classes(self) -> Iterable[type[MatchT_co]]:
        return iter(self._match_classes)

    @override
    def to_mismatch_classes(self, /) -> Iterable[type[MismatchT_co]]:
        return iter(self._mismatch_classes)

    @override
    def to_seed_mismatch(self, rule_name: str | None, /) -> MismatchT_co:
        return self.resolve().expression.to_seed_mismatch(rule_name)  # type: ignore[misc]

    __slots__ = (
        '_match_classes',
        '_mismatch_classes',
        '_name',
        '_referent_name',
        '_rules',
    )

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {RuleReference.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls,
        name: str,
        referent_name: str,
        /,
        *,
        match_classes: Sequence[type[MatchT_co]],
        mismatch_classes: Sequence[type[MismatchT_co]],
        rules: Mapping[str, Rule[MatchT_co, MismatchT_co]],
    ) -> Self:
        assert len(name) > 0, name
        self = super().__new__(cls)
        (
            self._match_classes,
            self._mismatch_classes,
            self._name,
            self._referent_name,
            self._rules,
        ) = (match_classes, mismatch_classes, name, referent_name, rules)
        return self

    _match_classes: Sequence[type[MatchT_co]]
    _mismatch_classes: Sequence[type[MismatchT_co]]
    _name: str
    _referent_name: str
    _rules: Mapping[str, Rule[MatchT_co, MismatchT_co]]

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


@final
class SequenceExpression(Expression[MatchTree, MismatchTree]):
    @classmethod
    @override
    def precedence(cls, /) -> int:
        return ExpressionPrecedence.SEQUENCE

    @property
    def elements(self, /) -> Sequence[Expression[AnyMatch, AnyMismatch]]:
        return self._elements

    @override
    def equals_to(
        self, other: Expression[Any, Any], /, *, visited_rule_names: set[str]
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
        cache: dict[str, dict[int, AnyMatch | AnyMismatch]],
        rule_name: str | None,
    ) -> MatchTree | MismatchTree:
        non_lookahead_matches: list[MatchLeaf | MatchTree] = []
        for element in self._elements:
            element_match = element.evaluate(
                text, index, cache=cache, rule_name=None
            )
            if is_mismatch(element_match):
                return MismatchTree(
                    rule_name, children=[*non_lookahead_matches, element_match]
                )
            else:
                if isinstance(element_match, LookaheadMatch):
                    continue
                assert isinstance(element_match, MatchLeaf | MatchTree), (
                    element_match
                )  # fmt: skip
                non_lookahead_matches.append(element_match)
                index += element_match.characters_count
        assert len(non_lookahead_matches) > 0, non_lookahead_matches
        return MatchTree(rule_name, children=non_lookahead_matches)

    @override
    def to_match_classes(self, /) -> Iterable[type[MatchTree]]:
        yield MatchTree

    def to_mismatch_classes(self, /) -> Iterable[type[MismatchTree]]:
        yield MismatchTree

    @override
    def to_seed_mismatch(self, rule_name: str | None, /) -> MismatchTree:
        return MismatchTree(
            rule_name, children=[MismatchLeaf(None, characters='')]
        )

    __slots__ = ('_elements',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {SequenceExpression.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls, elements: Sequence[Expression[AnyMatch, AnyMismatch]], /
    ) -> Self:
        if not any(
            _is_progressing_expression(element) for element in elements
        ):
            raise ValueError(elements)
        assert len(elements) > 1, elements
        self = super().__new__(cls)
        self._elements = elements
        return self

    _elements: Sequence[Expression[AnyMatch, AnyMismatch]]

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._elements!r})'

    @override
    def __str__(self, /) -> str:
        parent_precedence = self.precedence()
        return ' '.join(
            _to_nested_expression_str(
                element, parent_precedence=parent_precedence
            )
            for element in self._elements
        )


@final
class ZeroOrMoreExpression(Expression[LookaheadMatch | MatchTree, NoMismatch]):
    @classmethod
    @override
    def precedence(cls, /) -> int:
        return ExpressionPrecedence.REPETITION

    @property
    def expression(self, /) -> Expression[MatchLeaf | MatchTree, AnyMismatch]:
        return self._expression

    @override
    def equals_to(
        self, other: Expression[Any, Any], /, *, visited_rule_names: set[str]
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
        cache: dict[str, dict[int, AnyMatch | AnyMismatch]],
        rule_name: str | None,
    ) -> LookaheadMatch | MatchTree:
        children: list[MatchLeaf | MatchTree] = []
        expression = self._expression
        while not is_mismatch(
            match := expression.evaluate(
                text, index, cache=cache, rule_name=None
            )
        ):
            assert isinstance(match, MatchLeaf | MatchTree), match
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
    def to_mismatch_classes(self, /) -> Iterable[type[NoMismatch]]:
        yield from ()

    @override
    def to_seed_mismatch(self, rule_name: str | None, /) -> NoMismatch:
        raise ValueError(self)

    __slots__ = ('_expression',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {ZeroOrMoreExpression.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls, expression: Expression[MatchLeaf | MatchTree, AnyMismatch], /
    ) -> Self:
        _validate_expression(expression)
        _validate_progressing_expression(expression)
        self = super().__new__(cls)
        self._expression = expression
        return self

    _expression: Expression[MatchLeaf | MatchTree, AnyMismatch]

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression!r})'

    @override
    def __str__(self, /) -> str:
        expression_str = _to_nested_expression_str(
            self._expression, parent_precedence=self.precedence()
        )
        return f'{expression_str}*'


@final
class ZeroRepetitionRangeExpression(
    Expression[LookaheadMatch | MatchTree, NoMismatch]
):
    MIN_END: ClassVar[int] = 2

    @classmethod
    @override
    def precedence(cls, /) -> int:
        return ExpressionPrecedence.REPETITION

    @property
    def end(self, /) -> int:
        return self._end

    @property
    def expression(self, /) -> Expression[MatchLeaf | MatchTree, AnyMismatch]:
        return self._expression

    @override
    def equals_to(
        self, other: Expression[Any, Any], /, *, visited_rule_names: set[str]
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
        cache: dict[str, dict[int, AnyMatch | AnyMismatch]],
        rule_name: str | None,
    ) -> LookaheadMatch | MatchTree | NoMismatch:
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
    def to_mismatch_classes(self, /) -> Iterable[type[NoMismatch]]:
        yield from ()

    @override
    def to_seed_mismatch(self, rule_name: str | None, /) -> NoMismatch:
        raise ValueError(self)

    __slots__ = '_end', '_expression'

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {ZeroRepetitionRangeExpression.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls,
        expression: Expression[MatchLeaf | MatchTree, AnyMismatch],
        end: int,
        /,
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

    _end: int
    _expression: Expression[MatchLeaf | MatchTree, AnyMismatch]

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression!r})'

    @override
    def __str__(self, /) -> str:
        expression_str = _to_nested_expression_str(
            self._expression, parent_precedence=self.precedence()
        )
        return f'{expression_str}{{,{self._end}}}'


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
    value: Expression[Any, Any], /
) -> TypeIs[Expression[MatchLeaf | MatchTree, AnyMismatch]]:
    return not any(
        issubclass(match_cls, LookaheadMatch)
        for match_cls in value.to_match_classes()
    )


def _to_nested_expression_str(
    value: Expression[Any, Any], /, *, parent_precedence: int
) -> str:
    return (
        f'({value})' if parent_precedence >= value.precedence() else str(value)
    )


def _validate_expression(value: Any, /) -> None:
    if not isinstance(value, Expression):
        raise TypeError(type(value))


def _validate_progressing_expression(value: Expression[Any, Any], /) -> None:
    if not _is_progressing_expression(value):
        raise ValueError(
            f'Expected progressing expression, but got {value!r}.'
        )


def _validate_repetition_bound(value: Any, /) -> None:
    if not isinstance(value, int):
        raise TypeError(type(value))
