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
from .match import (
    AnyMatch,
    LookaheadMatch,
    MatchLeaf,
    MatchT_co,
    MatchTree,
    MatchTreeChild,
    RuleMatch,
    is_match_tree_child,
)
from .mismatch import AnyMismatch, MismatchLeaf, MismatchT_co, MismatchTree

if TYPE_CHECKING:
    from .rule import Rule


@unique
class ExpressionPrecedence(IntEnum):
    PRIORITIZED_CHOICE = auto()
    SEQUENCE = auto()
    REPETITION = auto()
    LOOKAHEAD = auto()
    TERM = auto()


class EvaluationResult(ABC, Generic[MatchT_co, MismatchT_co]):
    @property
    @abstractmethod
    def match(self, /) -> MatchT_co | None:
        raise NotImplementedError

    @property
    @abstractmethod
    def mismatch(self, /) -> MismatchT_co | None:
        raise NotImplementedError

    @abstractmethod
    def __repr__(self, /) -> str:
        raise NotImplementedError


@final
class EvaluationSuccess(EvaluationResult[MatchT_co, MismatchT_co]):
    @property
    @override
    def match(self, /) -> MatchT_co:
        return self._match

    @property
    @override
    def mismatch(self, /) -> MismatchT_co | None:
        return self._mismatch

    _match: MatchT_co
    _mismatch: MismatchT_co | None

    __slots__ = '_match', '_mismatch'

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {EvaluationSuccess.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls, match: MatchT_co, mismatch: MismatchT_co | None, /
    ) -> Self:
        self = super().__new__(cls)
        self._match, self._mismatch = match, mismatch
        return self

    @override
    def __repr__(self, /) -> str:
        return (
            f'{type(self).__qualname__}({self._match!r}, {self._mismatch!r})'
        )


@final
class EvaluationFailure(EvaluationResult[Any, MismatchT_co]):
    @property
    @override
    def match(self, /) -> None:
        return None

    @property
    @override
    def mismatch(self, /) -> MismatchT_co:
        return self._mismatch

    _mismatch: MismatchT_co

    __slots__ = ('_mismatch',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {EvaluationFailure.__qualname__!r} '
            'is not an acceptable base type'
        )

    @override
    def __new__(cls, mismatch: MismatchT_co, /) -> Self:
        self = super().__new__(cls)
        self._mismatch = mismatch
        return self

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._mismatch!r})'


class Expression(ABC, Generic[MatchT_co, MismatchT_co]):
    __slots__ = ()

    @classmethod
    @abstractmethod
    def precedence(cls, /) -> int:
        raise NotImplementedError

    @abstractmethod
    def evaluate(
        self, text: str, index: int, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationResult[MatchT_co, MismatchT_co]:
        raise NotImplementedError

    def is_valid_match(self, value: AnyMatch, /) -> TypeGuard[MatchT_co]:
        return any(
            isinstance(value, match_cls)
            for match_cls in self.to_match_classes()
        )

    def is_valid_mismatch(
        self, value: AnyMismatch, /
    ) -> TypeGuard[MismatchT_co]:
        return any(
            isinstance(value, mismatch_cls)
            for mismatch_cls in self.to_mismatch_classes()
        )

    def is_valid_result(
        self, value: EvaluationResult[Any, Any], /
    ) -> TypeGuard[EvaluationResult[MatchT_co, MismatchT_co]]:
        return (
            (match := value.match) is None or self.is_valid_match(match)
        ) and (
            (mismatch := value.mismatch) is None
            or self.is_valid_mismatch(mismatch)
        )

    @abstractmethod
    def to_expected_message(self, /, *, rules: Mapping[str, Rule]) -> str:
        raise NotImplementedError

    @abstractmethod
    def to_match_classes(self, /) -> Iterable[type[MatchT_co]]:
        raise NotImplementedError

    @abstractmethod
    def to_mismatch_classes(self, /) -> Iterable[type[MismatchT_co]]:
        raise NotImplementedError

    @abstractmethod
    def to_seed_failure(
        self, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationFailure[MismatchT_co]:
        raise NotImplementedError

    @overload
    def __eq__(self, other: Self, /) -> bool: ...

    @overload
    def __eq__(self, other: Any, /) -> Any: ...

    @abstractmethod
    def __eq__(self, other: Any, /) -> Any:
        raise NotImplementedError

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
    def evaluate(
        self, text: str, index: int, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationResult[MatchLeaf, MismatchLeaf]:
        return (
            EvaluationSuccess(MatchLeaf(characters=text[index]), None)
            if index < len(text)
            else EvaluationFailure(
                MismatchLeaf(
                    str(self),
                    expected_message=self.to_expected_message(rules=rules),
                    start_index=index,
                    stop_index=index + 1,
                )
            )
        )

    @override
    def to_expected_message(self, /, *, rules: Mapping[str, Rule]) -> str:
        return 'any character'

    @override
    def to_match_classes(self, /) -> Iterable[type[MatchLeaf]]:
        yield MatchLeaf

    @override
    def to_mismatch_classes(self, /) -> Iterable[type[MismatchLeaf]]:
        yield MismatchLeaf

    @override
    def to_seed_failure(
        self, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationFailure[MismatchLeaf]:
        return EvaluationFailure(
            MismatchLeaf(
                str(self), expected_message='', start_index=0, stop_index=1
            )
        )

    __slots__ = ()

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {AnyCharacterExpression.__qualname__!r} '
            'is not an acceptable base type'
        )

    @overload
    def __eq__(self, other: Self, /) -> bool: ...

    @overload
    def __eq__(self, other: Any, /) -> Any: ...

    @override
    def __eq__(self, other: Any, /) -> Any:
        return isinstance(other, AnyCharacterExpression) or NotImplemented

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
    def evaluate(
        self, text: str, index: int, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationResult[MatchLeaf, MismatchLeaf]:
        if index >= len(text):
            return EvaluationFailure(
                MismatchLeaf(
                    str(self),
                    expected_message=self.to_expected_message(rules=rules),
                    start_index=index,
                    stop_index=index + 1,
                )
            )
        character = text[index]
        return (
            EvaluationSuccess(MatchLeaf(characters=character), None)
            if any(character in element for element in self._elements)
            else EvaluationFailure(
                MismatchLeaf(
                    str(self),
                    expected_message=self.to_expected_message(rules=rules),
                    start_index=index,
                    stop_index=index + 1,
                )
            )
        )

    @override
    def to_expected_message(self, /, *, rules: Mapping[str, Rule]) -> str:
        return f'a character from {self}'

    @override
    def to_match_classes(self, /) -> Iterable[type[MatchLeaf]]:
        yield MatchLeaf

    @override
    def to_mismatch_classes(self, /) -> Iterable[type[MismatchLeaf]]:
        yield MismatchLeaf

    @override
    def to_seed_failure(
        self, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationFailure[MismatchLeaf]:
        return EvaluationFailure(
            MismatchLeaf(
                str(self), expected_message='', start_index=0, stop_index=1
            )
        )

    _elements: Sequence[CharacterRange | CharacterSet]

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

    @overload
    def __eq__(self, other: Self, /) -> bool: ...

    @overload
    def __eq__(self, other: Any, /) -> Any: ...

    @override
    def __eq__(self, other: Any, /) -> Any:
        return (
            self._elements == other._elements
            if isinstance(other, CharacterClassExpression)
            else NotImplemented
        )

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
    def evaluate(
        self, text: str, index: int, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationResult[MatchLeaf, MismatchLeaf]:
        if index >= len(text):
            return EvaluationFailure(
                MismatchLeaf(
                    str(self),
                    expected_message=self.to_expected_message(rules=rules),
                    start_index=index,
                    stop_index=index + 1,
                )
            )
        character = text[index]
        return (
            EvaluationSuccess(MatchLeaf(characters=character), None)
            if all(character not in element for element in self._elements)
            else EvaluationFailure(
                MismatchLeaf(
                    str(self),
                    expected_message=self.to_expected_message(rules=rules),
                    start_index=index,
                    stop_index=index + 1,
                )
            )
        )

    @override
    def to_expected_message(self, /, *, rules: Mapping[str, Rule]) -> str:
        return f'a character from {self}'

    @override
    def to_match_classes(self, /) -> Iterable[type[MatchLeaf]]:
        yield MatchLeaf

    @override
    def to_mismatch_classes(self, /) -> Iterable[type[MismatchLeaf]]:
        yield MismatchLeaf

    @override
    def to_seed_failure(
        self, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationFailure[MismatchLeaf]:
        return EvaluationFailure(
            MismatchLeaf(
                str(self), expected_message='', start_index=0, stop_index=1
            )
        )

    _elements: Sequence[CharacterRange | CharacterSet]

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

    @overload
    def __eq__(self, other: Self, /) -> bool: ...

    @overload
    def __eq__(self, other: Any, /) -> Any: ...

    @override
    def __eq__(self, other: Any, /) -> Any:
        return (
            self._elements == other._elements
            if isinstance(other, ComplementedCharacterClassExpression)
            else NotImplemented
        )

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
    def expression(self, /) -> Expression[MatchTreeChild, AnyMismatch]:
        return self._expression

    @override
    def evaluate(
        self, text: str, index: int, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationResult[MatchTree, MismatchTree]:
        children: list[MatchTreeChild] = []
        expression = self._expression
        for _ in range(self._count):
            result = expression.evaluate(text, index, rules=rules)
            if (match := result.match) is not None:
                assert is_match_tree_child(match), (expression, result)
                children.append(match)
                index += match.characters_count
            else:
                assert is_failure(result), (expression, result)
                return EvaluationFailure(
                    MismatchTree(str(self), children=[result.mismatch])
                )
        return EvaluationSuccess(MatchTree(children=children), None)

    @override
    def to_expected_message(self, /, *, rules: Mapping[str, Rule]) -> str:
        return (
            f'{self._expression.to_expected_message(rules=rules)} '
            f'repeated {self._count} times'
        )

    @override
    def to_match_classes(self, /) -> Iterable[type[MatchTree]]:
        yield MatchTree

    @override
    def to_mismatch_classes(self, /) -> Iterable[type[MismatchTree]]:
        yield MismatchTree

    @override
    def to_seed_failure(
        self, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationFailure[MismatchTree]:
        return EvaluationFailure(
            MismatchTree(
                str(self),
                children=[
                    MismatchLeaf(
                        str(self._expression),
                        expected_message='',
                        start_index=0,
                        stop_index=1,
                    )
                ],
            )
        )

    _count: int
    _expression: Expression[MatchTreeChild, AnyMismatch]

    __slots__ = '_count', '_expression'

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {ExactRepetitionExpression.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls, expression: Expression[MatchTreeChild, AnyMismatch], count: int, /
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

    @overload
    def __eq__(self, other: Self, /) -> bool: ...

    @overload
    def __eq__(self, other: Any, /) -> Any: ...

    @override
    def __eq__(self, other: Any, /) -> Any:
        return (
            (
                self._count == other._count
                and self._expression == other._expression
            )
            if isinstance(other, ExactRepetitionExpression)
            else NotImplemented
        )

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
    def evaluate(
        self, text: str, index: int, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationResult[MatchLeaf, MismatchLeaf]:
        return (
            EvaluationFailure(
                MismatchLeaf(
                    str(self),
                    expected_message=self.to_expected_message(rules=rules),
                    start_index=index,
                    stop_index=index + 1,
                )
            )
            if text[index : index + len(self.characters)] != self.characters
            else EvaluationSuccess(MatchLeaf(characters=self.characters), None)
        )

    @override
    def to_expected_message(self, /, *, rules: Mapping[str, Rule]) -> str:
        return repr(self.characters)

    @override
    def to_match_classes(self, /) -> Iterable[type[MatchLeaf]]:
        yield MatchLeaf

    @override
    def to_mismatch_classes(self, /) -> Iterable[type[MismatchLeaf]]:
        yield MismatchLeaf

    @override
    def to_seed_failure(
        self, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationFailure[MismatchLeaf]:
        return EvaluationFailure(
            MismatchLeaf(
                str(self), expected_message='', start_index=0, stop_index=1
            )
        )

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

    __slots__ = ()

    @overload
    def __eq__(self, other: Self, /) -> bool: ...

    @overload
    def __eq__(self, other: Any, /) -> Any: ...

    @override
    def __eq__(self, other: Any, /) -> Any:
        return (
            self.characters == other.characters
            if isinstance(other, type(self))
            else NotImplemented
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

    _characters: str

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

    _characters: str

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

    @override
    def __str__(self, /) -> str:
        return (
            f"'{_escape_single_quoted_literal_characters(self._characters)}'"
        )


@final
class NegativeLookaheadExpression(Expression[LookaheadMatch, MismatchLeaf]):
    @classmethod
    @override
    def precedence(cls, /) -> int:
        return ExpressionPrecedence.LOOKAHEAD

    @property
    def expression(self, /) -> Expression[MatchTreeChild, AnyMismatch]:
        return self._expression

    @override
    def evaluate(
        self, text: str, index: int, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationResult[LookaheadMatch, MismatchLeaf]:
        result = self._expression.evaluate(text, index, rules=rules)
        if is_success(result):
            return EvaluationFailure(
                MismatchLeaf(
                    str(self),
                    expected_message=self.to_expected_message(rules=rules),
                    start_index=index,
                    stop_index=index + result.match.characters_count,
                )
            )
        assert is_failure(result), (self._expression, result)
        return EvaluationSuccess(LookaheadMatch(), result.mismatch)

    @override
    def to_expected_message(self, /, *, rules: Mapping[str, Rule]) -> str:
        return f'not {self._expression.to_expected_message(rules=rules)}'

    @override
    def to_match_classes(self, /) -> Iterable[type[LookaheadMatch]]:
        yield LookaheadMatch

    @override
    def to_mismatch_classes(self, /) -> Iterable[type[MismatchLeaf]]:
        yield MismatchLeaf

    @override
    def to_seed_failure(
        self, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationFailure[MismatchLeaf]:
        return EvaluationFailure(
            MismatchLeaf(
                str(self), expected_message='', start_index=0, stop_index=1
            )
        )

    _expression: Expression[MatchTreeChild, AnyMismatch]

    __slots__ = ('_expression',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {NegativeLookaheadExpression.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls, expression: Expression[MatchTreeChild, AnyMismatch], /
    ) -> Self:
        _validate_expression(expression)
        _validate_progressing_expression(expression)
        self = super().__new__(cls)
        self._expression = expression
        return self

    @overload
    def __eq__(self, other: Self, /) -> bool: ...

    @overload
    def __eq__(self, other: Any, /) -> Any: ...

    @override
    def __eq__(self, other: Any, /) -> Any:
        return (
            self._expression == other._expression
            if isinstance(other, NegativeLookaheadExpression)
            else NotImplemented
        )

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
    def expression(self, /) -> Expression[MatchTreeChild, AnyMismatch]:
        return self._expression

    @override
    def evaluate(
        self, text: str, index: int, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationResult[MatchTree, MismatchTree]:
        expression = self._expression
        first_result = expression.evaluate(text, index, rules=rules)
        matches: list[MatchTreeChild]
        if is_success(first_result):
            first_match = first_result.match
            assert is_match_tree_child(first_match), (expression, first_result)
            matches = [first_match]
            index += first_match.characters_count
        else:
            assert is_failure(first_result), (expression, first_result)
            return EvaluationFailure(
                MismatchTree(str(self), children=[first_result.mismatch])
            )
        while is_success(
            result := expression.evaluate(text, index, rules=rules)
        ):
            match = result.match
            matches.append(match)
            assert is_match_tree_child(match), (expression, result)
            index += match.characters_count
        assert is_failure(result), (expression, result)
        return EvaluationSuccess(
            MatchTree(children=matches),
            MismatchTree(str(self), children=[result.mismatch]),
        )

    @override
    def to_expected_message(self, /, *, rules: Mapping[str, Rule]) -> str:
        return (
            f'{self._expression.to_expected_message(rules=rules)} '
            'repeated at least once'
        )

    @override
    def to_match_classes(self, /) -> Iterable[type[MatchTree]]:
        yield MatchTree

    def to_mismatch_classes(self, /) -> Iterable[type[MismatchTree]]:
        yield MismatchTree

    @override
    def to_seed_failure(
        self, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationFailure[MismatchTree]:
        return EvaluationFailure(
            MismatchTree(
                str(self),
                children=[
                    MismatchLeaf(
                        str(self._expression),
                        expected_message='',
                        start_index=0,
                        stop_index=1,
                    )
                ],
            )
        )

    _expression: Expression[MatchTreeChild, AnyMismatch]

    __slots__ = ('_expression',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {OneOrMoreExpression.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls, expression: Expression[MatchTreeChild, AnyMismatch], /
    ) -> Self:
        _validate_expression(expression)
        _validate_progressing_expression(expression)
        self = super().__new__(cls)
        self._expression = expression
        return self

    @overload
    def __eq__(self, other: Self, /) -> bool: ...

    @overload
    def __eq__(self, other: Any, /) -> Any: ...

    @override
    def __eq__(self, other: Any, /) -> Any:
        return (
            self._expression == other._expression
            if isinstance(other, OneOrMoreExpression)
            else NotImplemented
        )

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
class OptionalExpression(Expression[AnyMatch, AnyMismatch]):
    @classmethod
    @override
    def precedence(cls, /) -> int:
        return ExpressionPrecedence.REPETITION

    @property
    def expression(self, /) -> Expression[MatchTreeChild, AnyMismatch]:
        return self._expression

    @override
    def evaluate(
        self, text: str, index: int, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationSuccess[AnyMatch, AnyMismatch]:
        result = self._expression.evaluate(text, index, rules=rules)
        if is_success(result):
            return result
        assert is_failure(result), (self._expression, result)
        return EvaluationSuccess(LookaheadMatch(), result.mismatch)

    def to_expected_message(self, /, *, rules: Mapping[str, Rule]) -> str:
        return (
            f'{self._expression.to_expected_message(rules=rules)} '
            'repeated at most once'
        )

    @override
    def to_match_classes(self, /) -> Iterable[type[AnyMatch]]:
        yield LookaheadMatch
        yield from self._expression.to_match_classes()

    @override
    def to_mismatch_classes(self, /) -> Iterable[type[AnyMismatch]]:
        yield from self._expression.to_mismatch_classes()

    @override
    def to_seed_failure(
        self, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationFailure[AnyMismatch]:
        raise ValueError(self)

    _expression: Expression[MatchTreeChild, AnyMismatch]

    __slots__ = ('_expression',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {OptionalExpression.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls, expression: Expression[MatchTreeChild, AnyMismatch], /
    ) -> Self:
        _validate_expression(expression)
        _validate_progressing_expression(expression)
        self = super().__new__(cls)
        self._expression = expression
        return self

    @overload
    def __eq__(self, other: Self, /) -> bool: ...

    @overload
    def __eq__(self, other: Any, /) -> Any: ...

    @override
    def __eq__(self, other: Any, /) -> Any:
        return (
            self._expression == other._expression
            if isinstance(other, OptionalExpression)
            else NotImplemented
        )

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
class PositiveLookaheadExpression(Expression[LookaheadMatch, MismatchLeaf]):
    @classmethod
    @override
    def precedence(cls, /) -> int:
        return ExpressionPrecedence.LOOKAHEAD

    @property
    def expression(self, /) -> Expression[MatchTreeChild, AnyMismatch]:
        return self._expression

    @override
    def evaluate(
        self, text: str, index: int, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationResult[LookaheadMatch, MismatchLeaf]:
        result = self._expression.evaluate(text, index, rules=rules)
        if is_failure(result):
            assert result.mismatch.start_index == index, (
                self._expression,
                result,
            )
            return EvaluationFailure(
                MismatchLeaf(
                    str(self),
                    expected_message=self.to_expected_message(rules=rules),
                    start_index=index,
                    stop_index=result.mismatch.stop_index,
                )
            )
        return EvaluationSuccess(LookaheadMatch(), None)

    @override
    def to_expected_message(self, /, *, rules: Mapping[str, Rule]) -> str:
        return self._expression.to_expected_message(rules=rules)

    @override
    def to_match_classes(self, /) -> Iterable[type[LookaheadMatch]]:
        yield LookaheadMatch

    @override
    def to_mismatch_classes(self, /) -> Iterable[type[MismatchLeaf]]:
        yield MismatchLeaf

    @override
    def to_seed_failure(
        self, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationFailure[MismatchLeaf]:
        return EvaluationFailure(
            MismatchLeaf(
                str(self), expected_message='', start_index=0, stop_index=1
            )
        )

    _expression: Expression[MatchTreeChild, AnyMismatch]

    __slots__ = ('_expression',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {PositiveLookaheadExpression.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls, expression: Expression[MatchTreeChild, AnyMismatch], /
    ) -> Self:
        _validate_expression(expression)
        _validate_progressing_expression(expression)
        self = super().__new__(cls)
        self._expression = expression
        return self

    @overload
    def __eq__(self, other: Self, /) -> bool: ...

    @overload
    def __eq__(self, other: Any, /) -> Any: ...

    @override
    def __eq__(self, other: Any, /) -> Any:
        return (
            self._expression == other._expression
            if isinstance(other, PositiveLookaheadExpression)
            else NotImplemented
        )

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
    def expression(self, /) -> Expression[MatchTreeChild, AnyMismatch]:
        return self._expression

    @property
    def start(self, /) -> int:
        return self._start

    @override
    def evaluate(
        self, text: str, index: int, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationResult[MatchTree, MismatchTree]:
        children: list[MatchTreeChild] = []
        expression = self._expression
        for _ in range(self._start):
            result = expression.evaluate(text, index, rules=rules)
            if (match := result.match) is not None:
                assert is_match_tree_child(match), (expression, result)
                children.append(match)
                index += match.characters_count
            else:
                assert is_failure(result), (expression, result)
                return EvaluationFailure(
                    MismatchTree(str(self), children=[result.mismatch])
                )
        while is_success(
            result := expression.evaluate(text, index, rules=rules)
        ):
            match = result.match
            assert is_match_tree_child(match), (expression, result)
            children.append(match)
            index += match.characters_count
        assert is_failure(result), (expression, result)
        return EvaluationSuccess(MatchTree(children=children), result.mismatch)

    @override
    def to_expected_message(self, /, *, rules: Mapping[str, Rule]) -> str:
        return (
            f'{self._expression.to_expected_message(rules=rules)} '
            f'repeated at least {self._start} times'
        )

    @override
    def to_match_classes(self, /) -> Iterable[type[MatchTree]]:
        yield MatchTree

    @override
    def to_mismatch_classes(self, /) -> Iterable[type[MismatchTree]]:
        yield MismatchTree

    @override
    def to_seed_failure(
        self, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationFailure[MismatchTree]:
        return EvaluationFailure(
            MismatchTree(
                str(self),
                children=[
                    MismatchLeaf(
                        str(self._expression),
                        expected_message='',
                        start_index=0,
                        stop_index=1,
                    )
                ],
            )
        )

    _expression: Expression[MatchTreeChild, AnyMismatch]
    _start: int

    __slots__ = '_expression', '_start'

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {PositiveOrMoreExpression.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls, expression: Expression[MatchTreeChild, AnyMismatch], start: int, /
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

    @overload
    def __eq__(self, other: Self, /) -> bool: ...

    @overload
    def __eq__(self, other: Any, /) -> Any: ...

    @override
    def __eq__(self, other: Any, /) -> Any:
        return (
            (
                self._start == other._start
                and self._expression == other._expression
            )
            if isinstance(other, PositiveOrMoreExpression)
            else NotImplemented
        )

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
    def expression(self, /) -> Expression[MatchTreeChild, AnyMismatch]:
        return self._expression

    @property
    def start(self, /) -> int:
        return self._start

    @override
    def evaluate(
        self, text: str, index: int, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationResult[MatchTree, MismatchTree]:
        matches: list[MatchTreeChild] = []
        expression = self._expression
        for _ in range(self._start):
            result = expression.evaluate(text, index, rules=rules)
            if is_success(result):
                match = result.match
                assert is_match_tree_child(match), (expression, result)
                matches.append(match)
                index += match.characters_count
            else:
                assert is_failure(result), (expression, result)
                return EvaluationFailure(
                    MismatchTree(str(self), children=[result.mismatch])
                )
        final_mismatch: AnyMismatch | None = None
        for _ in range(self._start, self._end):
            result = expression.evaluate(text, index, rules=rules)
            assert self.is_valid_result(result)
            if is_success(result):
                match = result.match
                assert is_match_tree_child(match), (expression, result)
                matches.append(match)
                index += match.characters_count
            else:
                final_mismatch = result.mismatch
                break
        return EvaluationSuccess(
            MatchTree(children=matches),
            (
                None
                if final_mismatch is None
                else MismatchTree(str(self), children=[final_mismatch])
            ),
        )

    @override
    def to_expected_message(self, /, *, rules: Mapping[str, Rule]) -> str:
        return (
            f'{self._expression.to_expected_message(rules=rules)} '
            f'repeated from {self._start} to {self._end} times'
        )

    @override
    def to_match_classes(self, /) -> Iterable[type[MatchTree]]:
        yield MatchTree

    @override
    def to_mismatch_classes(self, /) -> Iterable[type[MismatchTree]]:
        yield MismatchTree

    @override
    def to_seed_failure(
        self, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationFailure[MismatchTree]:
        return EvaluationFailure(
            MismatchTree(
                str(self),
                children=[
                    MismatchLeaf(
                        str(self._expression),
                        expected_message='',
                        start_index=0,
                        stop_index=1,
                    )
                ],
            )
        )

    _expression: Expression[MatchTreeChild, AnyMismatch]
    _end: int
    _start: int

    __slots__ = '_end', '_expression', '_start'

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {PositiveRepetitionRangeExpression.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls,
        expression: Expression[MatchTreeChild, AnyMismatch],
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

    @overload
    def __eq__(self, other: Self, /) -> bool: ...

    @overload
    def __eq__(self, other: Any, /) -> Any: ...

    @override
    def __eq__(self, other: Any, /) -> Any:
        return (
            (
                self._start == other._start
                and self._end == other._end
                and self._expression == other._expression
            )
            if isinstance(other, PositiveRepetitionRangeExpression)
            else NotImplemented
        )

    @override
    def __repr__(self, /) -> str:
        return (
            f'{type(self).__qualname__}'
            '('
            f'{self._expression!r}, '
            f'{self._start!r}, '
            f'{self._end!r}'
            ')'
        )

    @override
    def __str__(self, /) -> str:
        expression_str = _to_nested_expression_str(
            self._expression, parent_precedence=self.precedence()
        )
        return f'{expression_str}{{{self._start},{self._end}}}'


@final
class PrioritizedChoiceExpression(Expression[AnyMatch, MismatchTree]):
    @classmethod
    @override
    def precedence(cls, /) -> int:
        return ExpressionPrecedence.PRIORITIZED_CHOICE

    @property
    def variants(self, /) -> Sequence[Expression[AnyMatch, AnyMismatch]]:
        return self._variants

    @override
    def evaluate(
        self, text: str, index: int, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationResult[MatchT_co, MismatchTree]:
        variant_mismatches: list[AnyMismatch] = []
        for variant in self._variants:
            variant_result = variant.evaluate(text, index, rules=rules)
            if is_success(variant_result):
                return variant_result
            else:
                assert is_failure(variant_result), (variant, variant_result)
                variant_mismatches.append(variant_result.mismatch)
        return EvaluationFailure(
            MismatchTree(str(self), children=variant_mismatches)
        )

    @override
    def to_expected_message(self, /, *, rules: Mapping[str, Rule]) -> str:
        return ' or '.join(
            variant.to_expected_message(rules=rules)
            for variant in self._variants
        )

    @override
    def to_match_classes(self, /) -> Iterable[type[AnyMatch]]:
        for variant in self._variants:
            yield from variant.to_match_classes()

    @override
    def to_mismatch_classes(self, /) -> Iterable[type[MismatchTree]]:
        yield MismatchTree

    @override
    def to_seed_failure(
        self, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationFailure[MismatchTree]:
        return EvaluationFailure(
            MismatchTree(
                str(self),
                children=[
                    MismatchLeaf(
                        str(self._variants[0]),
                        expected_message='',
                        start_index=0,
                        stop_index=1,
                    )
                ],
            )
        )

    _variants: Sequence[Expression[AnyMatch, AnyMismatch]]

    __slots__ = ('_variants',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {PrioritizedChoiceExpression.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls, variants: Sequence[Expression[AnyMatch, AnyMismatch]], /
    ) -> Self:
        assert len(variants) > 1, variants
        self = super().__new__(cls)
        self._variants = variants
        return self

    @overload
    def __eq__(self, other: Self, /) -> bool: ...

    @overload
    def __eq__(self, other: Any, /) -> Any: ...

    @override
    def __eq__(self, other: Any, /) -> Any:
        return (
            (
                len(self._variants) == len(other._variants)
                and all(
                    variant == other_variant
                    for variant, other_variant in zip(
                        self._variants, other._variants, strict=True
                    )
                )
            )
            if isinstance(other, PrioritizedChoiceExpression)
            else NotImplemented
        )

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
class RuleReference(Expression[RuleMatch, AnyMismatch]):
    @classmethod
    @override
    def precedence(cls, /) -> int:
        return ExpressionPrecedence.TERM

    @override
    def evaluate(
        self, text: str, index: int, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationResult[RuleMatch, AnyMismatch]:
        return self._resolve(rules=rules).parse(text, index, rules=rules)

    @override
    def to_expected_message(self, /, *, rules: Mapping[str, Rule]) -> str:
        return self._resolve(rules=rules).expression.to_expected_message(
            rules=rules
        )

    @override
    def to_match_classes(self, /) -> Iterable[type[RuleMatch]]:
        yield RuleMatch

    @override
    def to_mismatch_classes(self, /) -> Iterable[type[AnyMismatch]]:
        return iter(self._mismatch_classes)

    @override
    def to_seed_failure(
        self, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationFailure[AnyMismatch]:
        return self._resolve(rules=rules).expression.to_seed_failure(
            rules=rules
        )

    _mismatch_classes: Sequence[type[AnyMismatch]]
    _name: str

    def _resolve(self, /, *, rules: Mapping[str, Rule]) -> Rule:
        return rules[self._name]

    __slots__ = ('_mismatch_classes', '_name')

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {RuleReference.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls, name: str, /, *, mismatch_classes: Sequence[type[AnyMismatch]]
    ) -> Self:
        assert len(name) > 0, name
        assert len(mismatch_classes) > 0, mismatch_classes
        self = super().__new__(cls)
        self._mismatch_classes, self._name = mismatch_classes, name
        return self

    @overload
    def __eq__(self, other: Self, /) -> bool: ...

    @overload
    def __eq__(self, other: Any, /) -> Any: ...

    @override
    def __eq__(self, other: Any) -> Any:
        return (
            (
                self._name == other._name
                and self._mismatch_classes == other._mismatch_classes
            )
            if isinstance(other, RuleReference)
            else NotImplemented
        )

    @override
    def __repr__(self, /) -> str:
        return (
            f'{type(self).__qualname__}'
            '('
            f'{self._name!r}, '
            f'mismatch_classes={self._mismatch_classes!r}'
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
    def evaluate(
        self, text: str, index: int, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationResult[MatchTree, MismatchTree]:
        element_successes: list[EvaluationSuccess[AnyMatch, AnyMismatch]] = []
        for element in self._elements:
            element_result = element.evaluate(text, index, rules=rules)
            if is_success(element_result):
                element_successes.append(element_result)
                element_match = element_result.match
                if not is_match_tree_child(element_match):
                    continue
                index += element_match.characters_count
            else:
                assert is_failure(element_result), (element, element_result)
                element_mismatch = element_result.mismatch
                return EvaluationFailure(
                    MismatchTree(
                        str(self),
                        children=[
                            *[
                                prev_element_mismatch
                                for prev_element_success in element_successes
                                if (
                                    (
                                        prev_element_mismatch := (
                                            prev_element_success.mismatch
                                        )
                                    )
                                    is not None
                                )
                                and (
                                    prev_element_mismatch.stop_index
                                    == element_mismatch.stop_index
                                )
                            ],
                            element_mismatch,
                        ],
                    )
                )
        return EvaluationSuccess(
            MatchTree(
                children=[
                    element_success.match
                    for element_success in element_successes
                    if is_match_tree_child(element_success.match)
                ]
            ),
            None,
        )

    @override
    def to_expected_message(self, /, *, rules: Mapping[str, Rule]) -> str:
        return ' followed by '.join(
            element.to_expected_message(rules=rules)
            for element in self._elements
        )

    @override
    def to_match_classes(self, /) -> Iterable[type[MatchTree]]:
        yield MatchTree

    def to_mismatch_classes(self, /) -> Iterable[type[MismatchTree]]:
        yield MismatchTree

    @override
    def to_seed_failure(
        self, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationFailure[MismatchTree]:
        return EvaluationFailure(
            MismatchTree(
                str(self),
                children=[
                    MismatchLeaf(
                        str(self._elements[0]),
                        expected_message='',
                        start_index=0,
                        stop_index=1,
                    )
                ],
            )
        )

    _elements: Sequence[Expression[AnyMatch, AnyMismatch]]

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

    @overload
    def __eq__(self, other: Self, /) -> bool: ...

    @overload
    def __eq__(self, other: Any, /) -> Any: ...

    @override
    def __eq__(self, other: Any, /) -> Any:
        return (
            (
                len(self._elements) == len(other._elements)
                and all(
                    element == other_element
                    for element, other_element in zip(
                        self._elements, other._elements, strict=True
                    )
                )
            )
            if isinstance(other, SequenceExpression)
            else NotImplemented
        )

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
class ZeroOrMoreExpression(
    Expression[LookaheadMatch | MatchTree, MismatchTree]
):
    @classmethod
    @override
    def precedence(cls, /) -> int:
        return ExpressionPrecedence.REPETITION

    @property
    def expression(self, /) -> Expression[MatchTreeChild, AnyMismatch]:
        return self._expression

    @override
    def evaluate(
        self, text: str, index: int, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationSuccess[LookaheadMatch | MatchTree, MismatchTree]:
        matches: list[MatchTreeChild] = []
        expression = self._expression
        while is_success(
            result := expression.evaluate(text, index, rules=rules)
        ):
            match = result.match
            assert is_match_tree_child(match), (expression, result)
            matches.append(match)
            index += match.characters_count
        assert is_failure(result), (expression, result)
        return EvaluationSuccess(
            (
                LookaheadMatch()
                if len(matches) == 0
                else MatchTree(children=matches)
            ),
            MismatchTree(str(self), children=[result.mismatch]),
        )

    @override
    def to_expected_message(self, /, *, rules: Mapping[str, Rule]) -> str:
        return (
            f'{self._expression.to_expected_message(rules=rules)} '
            'repeated any amount of times or none at all'
        )

    @override
    def to_match_classes(
        self, /
    ) -> Iterable[type[LookaheadMatch | MatchTree]]:
        yield LookaheadMatch
        yield MatchTree

    @override
    def to_mismatch_classes(self, /) -> Iterable[type[MismatchTree]]:
        yield MismatchTree

    @override
    def to_seed_failure(
        self, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationFailure[MismatchTree]:
        return EvaluationFailure(
            MismatchTree(
                str(self),
                children=[
                    MismatchLeaf(
                        str(self._expression),
                        expected_message='',
                        start_index=0,
                        stop_index=1,
                    )
                ],
            )
        )

    _expression: Expression[MatchTreeChild, AnyMismatch]

    __slots__ = ('_expression',)

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {ZeroOrMoreExpression.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls, expression: Expression[MatchTreeChild, AnyMismatch], /
    ) -> Self:
        _validate_expression(expression)
        _validate_progressing_expression(expression)
        self = super().__new__(cls)
        self._expression = expression
        return self

    @overload
    def __eq__(self, other: Self, /) -> bool: ...

    @overload
    def __eq__(self, other: Any, /) -> Any: ...

    @override
    def __eq__(self, other: Any) -> Any:
        return (
            self._expression == other._expression
            if isinstance(other, ZeroOrMoreExpression)
            else NotImplemented
        )

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
    Expression[LookaheadMatch | MatchTree, AnyMismatch]
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
    def expression(self, /) -> Expression[MatchTreeChild, AnyMismatch]:
        return self._expression

    @override
    def evaluate(
        self, text: str, index: int, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationSuccess[LookaheadMatch | MatchTree, AnyMismatch]:
        matches: list[MatchTreeChild] = []
        expression = self._expression
        final_mismatch: AnyMismatch | None = None
        for _ in range(self._end):
            result = expression.evaluate(text, index, rules=rules)
            if is_success(result):
                match = result.match
                assert is_match_tree_child(match), (expression, result)
                matches.append(match)
                index += match.characters_count
            else:
                final_mismatch = result.mismatch
                break
        return EvaluationSuccess(
            (
                LookaheadMatch()
                if len(matches) == 0
                else MatchTree(children=matches)
            ),
            (
                final_mismatch
                if final_mismatch is None or len(matches) == 0
                else MismatchTree(str(self), children=[final_mismatch])
            ),
        )

    @override
    def to_expected_message(self, /, *, rules: Mapping[str, Rule]) -> str:
        return (
            f'{self._expression.to_expected_message(rules=rules)} '
            f'repeated at most {self._end} times'
        )

    @override
    def to_match_classes(
        self, /
    ) -> Iterable[type[LookaheadMatch | MatchTree]]:
        yield LookaheadMatch
        yield MatchTree

    @override
    def to_mismatch_classes(self, /) -> Iterable[type[AnyMismatch]]:
        yield from self._expression.to_mismatch_classes()

    @override
    def to_seed_failure(
        self, /, *, rules: Mapping[str, Rule]
    ) -> EvaluationFailure[AnyMismatch]:
        raise ValueError(self)

    _end: int
    _expression: Expression[MatchTreeChild, AnyMismatch]

    __slots__ = '_end', '_expression'

    def __init_subclass__(cls, /) -> None:
        raise TypeError(
            f'type {ZeroRepetitionRangeExpression.__qualname__!r} '
            'is not an acceptable base type'
        )

    def __new__(
        cls, expression: Expression[MatchTreeChild, AnyMismatch], end: int, /
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

    @overload
    def __eq__(self, other: Self, /) -> bool: ...

    @overload
    def __eq__(self, other: Any, /) -> Any: ...

    @override
    def __eq__(self, other: Any) -> Any:
        return (
            self._expression == other._expression
            if isinstance(other, ZeroRepetitionRangeExpression)
            else NotImplemented
        )

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self._expression!r})'

    @override
    def __str__(self, /) -> str:
        expression_str = _to_nested_expression_str(
            self._expression, parent_precedence=self.precedence()
        )
        return f'{expression_str}{{,{self._end}}}'


def is_failure(value: Any, /) -> TypeIs[EvaluationFailure[Any]]:
    return isinstance(value, EvaluationFailure)


def is_success(value: Any, /) -> TypeIs[EvaluationSuccess[Any, Any]]:
    return isinstance(value, EvaluationSuccess)


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
) -> TypeIs[Expression[MatchTreeChild, AnyMismatch]]:
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
