from hypothesis import given

from pagen.models import Grammar
from pagen.parsing import parse_grammar

from tests.strategies import grammar_strategy


@given(grammar_strategy)
def test_round_trip(grammar: Grammar) -> None:
    round_tripped_grammar = parse_grammar(str(grammar))

    assert grammar == round_tripped_grammar
