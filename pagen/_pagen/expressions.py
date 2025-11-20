from __future__ import annotations

from _operator import methodcaller
from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping, Sequence
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Generic, TypeGuard, final, overload

from typing_extensions import Self, override

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


class CharacterClassExpression(Expression[MatchLeaf]):
    __slots__ = ('_elements',)

    def __new__(
        cls, elements: Sequence[CharacterRange | CharacterSet], /
    ) -> Self:
        assert len(elements) > 0, elements
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
    __slots__ = ('_elements',)

    def __new__(
        cls, elements: Sequence[CharacterRange | CharacterSet], /
    ) -> Self:
        assert len(elements) > 0, elements
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


class LiteralExpression(Expression[MatchLeaf]):
    __slots__ = ()

    @property
    @abstractmethod
    def value(self, /) -> str:
        pass

    @override
    def equals_to(
        self, other: Expression[Any], /, *, visited_rule_names: set[str]
    ) -> bool:
        return isinstance(other, type(self)) and self.value == other.value

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
            MatchLeaf(rule_name, characters=self.value)
            if text[index : index + len(self.value)] == self.value
            else Mismatch(rule_name, index)
        )

    @override
    def to_match_classes(self, /) -> Iterable[type[MatchLeaf]]:
        yield MatchLeaf

    @override
    def to_nested_str(self, /) -> str:
        return self.__str__()

    @override
    def __repr__(self, /) -> str:
        return f'{type(self).__qualname__}({self.value!r})'


class DoubleQuotedLiteralExpression(LiteralExpression):
    __slots__ = ('_value',)

    def __new__(cls, value: str, /) -> Self:
        assert isinstance(value, str)
        assert len(value) > 0, value
        self = super().__new__(cls)
        self._value = value
        return self

    @property
    def value(self, /) -> str:
        return self._value

    _value: str

    @override
    def __str__(self, /) -> str:
        return f'"{_escape_double_quoted_literal_characters(self._value)}"'


class SingleQuotedLiteralExpression(LiteralExpression):
    __slots__ = ('_value',)

    def __new__(cls, value: str, /) -> Self:
        assert isinstance(value, str)
        assert len(value) > 0, value
        self = super().__new__(cls)
        self._value = value
        return self

    @property
    def value(self, /) -> str:
        return self._value

    _value: str

    @override
    def __str__(self, /) -> str:
        return f"'{_escape_single_quoted_literal_characters(self._value)}'"


class NegativeLookaheadExpression(Expression[LookaheadMatch]):
    __slots__ = ('_expression',)

    def __new__(cls, expression: Expression[MatchLeaf | MatchTree], /) -> Self:
        assert not any(
            issubclass(match_cls, LookaheadMatch)
            for match_cls in expression.to_match_classes()
        ), expression
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


class OneOrMoreExpression(Expression[MatchLeaf | MatchTree]):
    __slots__ = ('_expression',)

    def __new__(cls, expression: Expression[MatchLeaf | MatchTree], /) -> Self:
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
    ) -> MatchLeaf | MatchTree | Mismatch:
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
    def to_match_classes(self, /) -> Iterable[type[MatchLeaf | MatchTree]]:
        yield MatchLeaf
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
        result = self._expression.evaluate(
            text, index, cache=cache, rule_name=rule_name
        )
        return LookaheadMatch(rule_name) if is_mismatch(result) else result

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
        assert not any(
            issubclass(match_cls, LookaheadMatch)
            for match_cls in expression.to_match_classes()
        ), expression
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


class SequenceExpression(Expression[MatchLeaf | MatchTree]):
    __slots__ = ('_elements',)

    def __new__(cls, elements: Sequence[Expression[AnyMatch]], /) -> Self:
        assert len(elements) > 1, elements
        self = super().__new__(cls)
        self._elements = elements
        return self

    @property
    def expressions(self, /) -> Sequence[Expression[AnyMatch]]:
        return self._elements

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
    ) -> MatchLeaf | MatchTree | Mismatch:
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
    def to_match_classes(self, /) -> Iterable[type[MatchLeaf | MatchTree]]:
        yield MatchLeaf
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
