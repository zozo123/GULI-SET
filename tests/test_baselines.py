from gulliblebench.baselines import (
    naive_marketing_answer,
    naive_page_count_core_answer,
    oracle_core_answer,
)
from gulliblebench.dataset import generate_core_suite
from gulliblebench.evaluate import deterministic_baseline_results, summarize_core
from gulliblebench.marketing import MarketingAttack, generate_marketing_suite, make_marketing_case
from gulliblebench.world import Side


def test_oracle_core_is_perfect() -> None:
    cases = generate_core_suite()
    s = summarize_core(cases, {c.id: oracle_core_answer(c) for c in cases})
    assert s.strict_pass_rate == 1.0
    assert s.posterior_mae < 1e-12


def test_naive_core_is_hurt_by_echoes() -> None:
    cases = generate_core_suite()
    s = summarize_core(cases, {c.id: naive_page_count_core_answer(c) for c in cases})
    assert s.echo_posterior_mae > 0
    assert s.strict_pass_rate < 1.0


def test_naive_marketing_falls_for_manufactured_consensus() -> None:
    case = make_marketing_case(0, MarketingAttack.MANUFACTURED_CONSENSUS, target_side=Side.B)
    ans = naive_marketing_answer(case)
    assert ans.choice is Side.B
    assert ans.campaign_claim_supported is True


def test_baseline_dynamic_range() -> None:
    out = deterministic_baseline_results(generate_core_suite(), generate_marketing_suite())
    assert out["oracle"]["core"]["strict_pass_rate"] == 1.0
    assert out["naive-page-counter"]["marketing"]["strict_pass_rate"] < 1.0
