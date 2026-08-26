from math import isclose

from gulliblebench.dataset import generate_core_suite
from gulliblebench.generator import make_counterfactual_pair
from gulliblebench.oracle import bayes_posterior_b
from gulliblebench.render import render_core


def test_atomic_pair_invariant() -> None:
    echo, independent = make_counterfactual_pair(n_pages=4, reliability=0.75)
    assert len(echo.pages) == len(independent.pages) == 4
    assert len(echo.evidence_origins) == 1
    assert len(independent.evidence_origins) == 4
    assert isclose(bayes_posterior_b(0.5, echo.evidence_origins), 0.75)
    assert isclose(bayes_posterior_b(0.5, independent.evidence_origins), 81 / 82)


def test_default_core_size_and_balance() -> None:
    cases = generate_core_suite()
    assert len(cases) == 48
    assert sum(c.hidden.truth.value == "A" for c in cases) == 24


def test_prompt_has_oracle_inputs_not_truth_leak() -> None:
    echo, _ = make_counterfactual_pair(n_pages=4, reliability=0.75)
    prompt = render_core(echo).prompt
    assert "correct 75% of the time" in prompt
    assert "origin-1" in prompt
    assert "ground truth" not in prompt.lower()
