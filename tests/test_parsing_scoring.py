import pytest

from gulliblebench.generator import make_counterfactual_pair
from gulliblebench.parsing import parse_answer
from gulliblebench.scoring import ParsedAnswer, score_core
from gulliblebench.world import Side


def test_parse_core() -> None:
    a = parse_answer('{"probability_b":0.75,"independent_evidence_units":1,"choice":"B"}')
    assert a.choice is Side.B


def test_bad_choice_rejected() -> None:
    with pytest.raises(ValueError):
        parse_answer('{"probability_b":0.75,"independent_evidence_units":1,"choice":"C"}')


def test_perfect_core_score() -> None:
    echo, _ = make_counterfactual_pair(n_pages=4, reliability=0.75)
    s = score_core(echo, ParsedAnswer(0.75, 1, Side.B))
    assert s.posterior_abs_error == 0
    assert s.provenance_abs_error == 0
    assert s.choice_correct
