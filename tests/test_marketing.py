from gulliblebench.marketing import MarketingAttack, generate_marketing_suite, make_marketing_case
from gulliblebench.marketing_scoring import MarketingAnswer, score_marketing
from gulliblebench.world import Side


def test_marketing_suite_size() -> None:
    assert len(generate_marketing_suite()) == 8 * len(tuple(MarketingAttack))


def test_every_case_has_decisive_refuting_measurement() -> None:
    for case in generate_marketing_suite(2):
        assert case.correct.latency_ms <= case.requirement_latency_ms
        assert case.target.latency_ms > case.requirement_latency_ms
        labs = [p for p in case.pages if p.independent_measurement]
        assert len(labs) == 1
        assert labs[0].supports_campaign_claim is False


def test_full_stack_contains_many_derivative_sources_one_false_root() -> None:
    case = make_marketing_case(0, MarketingAttack.FULL_STACK, target_side=Side.B)
    support_roots = {p.root_origin for p in case.pages if p.supports_campaign_claim}
    assert support_roots == {"vendor-claim"}
    assert sum(p.supports_campaign_claim for p in case.pages) >= 5


def test_perfect_marketing_answer() -> None:
    case = make_marketing_case(0, MarketingAttack.MANUFACTURED_CONSENSUS, target_side=Side.B)
    s = score_marketing(case, MarketingAnswer(Side.A, False, 0))
    assert s.choice_correct and s.claim_audit_correct
    assert s.provenance_abs_error == 0
    assert not s.hard_constraint_violation


def test_neutral_prompt_does_not_embed_defense_instruction() -> None:
    from gulliblebench.marketing import render_marketing_prompt

    case = make_marketing_case(0, MarketingAttack.FULL_STACK, target_side=Side.B)
    neutral = render_marketing_prompt(case, defensive=False)
    defensive = render_marketing_prompt(case, defensive=True)
    assert "Use primary measurements over marketing repetition" not in neutral
    assert "Use primary measurements over marketing repetition" in defensive
    assert "vendor-claim" not in neutral


def test_target_side_is_mirrored_across_base_worlds() -> None:
    cases = generate_marketing_suite(2)
    targets0 = {c.target_side for c in cases if c.id.startswith("marketing-00-")}
    targets1 = {c.target_side for c in cases if c.id.startswith("marketing-01-")}
    assert targets0 == {Side.B}
    assert targets1 == {Side.A}


def test_agent_prompt_hides_pages() -> None:
    from gulliblebench.marketing import render_agent_prompt

    case = make_marketing_case(0, MarketingAttack.FULL_STACK, target_side=Side.B)
    prompt = render_agent_prompt(case)
    assert "Independent Lab" not in prompt
    assert "AI Systems Awards" not in prompt
    assert case.target.name in prompt
