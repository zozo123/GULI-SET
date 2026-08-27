"""Flip Cost invariants: exact minimality, oracle-freedom, and pinned ladder values.

The regression constants in this file are measured, not aspirational. They are pinned
so that any change to :data:`gulliblebench.flipcost.ACTION_COSTS`, to the reader
ladder, or to the marketing generator fails loudly instead of quietly restating a new
number as the result.
"""

from __future__ import annotations

import itertools
from functools import lru_cache
from statistics import mean

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from gulliblebench.flipcost import (
    ACTION_COSTS,
    READER_LADDER,
    AttackerAction,
    AttackerPlan,
    FlipCostResult,
    FlipPredicate,
    ReaderPolicy,
    apply_plan,
    enumerate_plans,
    flip_cost,
    is_flipped,
    summarize_flip_cost,
)
from gulliblebench.marketing import MarketingAttack, generate_marketing_suite, make_marketing_case
from gulliblebench.marketing_scoring import MarketingAnswer, score_marketing
from gulliblebench.meta_harness import PROVENANCE_LAYER
from gulliblebench.world import Side

#: An independent transcription of the pre-registered price table. Deliberately a
#: literal and not an import, so a silent edit to ACTION_COSTS is caught.
EXPECTED_PRICES = {
    "echo": 1,
    "seo_boost": 1,
    "launder": 3,
    "bury_lab": 5,
    "forge_measurement": 8,
}

#: Scope of the pinned ladder measurement.
LADDER_BUDGET = 16
LADDER_N = 64

#: Measured mean Flip Cost per ladder rung, over flippable cases only.
PINNED_MEAN = {
    "choice": (0.375, 0.375, 2.125, 2.125, 9.125),
    "audit": (0.375, 0.375, 0.375, 8, 8),
    "provenance": (0.375, 0.375, 0.375, 8, 8),
}
#: Measured share of cases the reader already gets wrong at zero attacker cost.
PINNED_ALREADY_FLIPPED = {
    "choice": (0.625, 0.625, 0.25, 0.25, 0.0),
    "audit": (0.625, 0.625, 0.625, 0.0, 0.0),
    "provenance": (0.625, 0.625, 0.625, 0.0, 0.0),
}
#: Measured share of cases not flippable within LADDER_BUDGET.
PINNED_UNFLIPPABLE = {
    "choice": (0.0, 0.0, 0.0, 0.0, 0.0),
    "audit": (0.0, 0.0, 0.0, 0.125, 0.0),
    "provenance": (0.0, 0.0, 0.0, 0.125, 0.0),
}
#: Measured CHOICE Flip Cost by attack for the top rung (+seek_primary_evidence).
PINNED_TOP_RUNG_CHOICE_BY_ATTACK = {
    "manufactured_consensus": 6,
    "full_stack": 7,
    "circular_citation": 8,
    "authority_laundering": 9,
    "benchmark_laundering": 9,
    "plain_false": 11,
    "unsupported_precision": 11,
    "selective_omission": 12,
}
#: Every minimal plan ever selected anywhere in the pinned ladder measurement.
PINNED_SELECTED_PLANS = frozenset(
    {
        "no action",
        "1xecho",
        "2xecho",
        "4xecho",
        "6xecho",
        "7xecho",
        "1xforge_measurement",
        "1xecho + 1xforge_measurement",
        "3xecho + 1xforge_measurement",
        "3xecho + 1xseo_boost + 1xforge_measurement",
        "none within budget",
    }
)

TOP_RUNG = READER_LADDER[-1]


@lru_cache(maxsize=1)
def _ladder_grid() -> dict[tuple[str, str], tuple[FlipCostResult, ...]]:
    """Every (predicate, reader) column of per-case results, computed exactly once."""

    cases = generate_marketing_suite()
    plans = enumerate_plans(LADDER_BUDGET)
    return {
        (predicate.value, reader.name): tuple(
            flip_cost(
                case, reader, predicate=predicate, max_budget=LADDER_BUDGET, plans=plans
            )
            for case in cases
        )
        for predicate in FlipPredicate
        for reader in READER_LADDER
    }


def _aggregate(results: tuple[FlipCostResult, ...]) -> tuple[float | None, float, float]:
    """Re-derive summarize_flip_cost's headline statistics independently."""

    costs = [r.cost for r in results if r.cost is not None]
    return (
        mean(costs) if costs else None,
        mean(float(r.already_flipped) for r in results),
        mean(float(not r.flipped) for r in results),
    )


def _brute_force_minimum(
    case, reader: ReaderPolicy, predicate: FlipPredicate, budget: int
) -> int | None:
    """Independent exhaustive search: build every plan, then take the cheapest flip."""

    ranges = [range(budget // price + 1) for price in EXPECTED_PRICES.values()]
    best: int | None = None
    for counts in itertools.product(*ranges):
        cost = sum(n * price for n, price in zip(counts, EXPECTED_PRICES.values(), strict=True))
        if cost > budget or (best is not None and cost >= best):
            continue
        echo, seo, launder, bury, forge = counts
        plan = AttackerPlan(echo, seo, launder, bury, forge)
        if is_flipped(case, reader.answer(apply_plan(case, plan)), predicate):
            best = cost
    return best


# --- 1. determinism -------------------------------------------------------------


def test_flip_cost_is_deterministic_across_repeated_calls() -> None:
    case = make_marketing_case(3, MarketingAttack.FULL_STACK, target_side=Side.A)
    for predicate in FlipPredicate:
        for reader in READER_LADDER:
            first = flip_cost(case, reader, predicate=predicate, max_budget=8)
            second = flip_cost(case, reader, predicate=predicate, max_budget=8)
            assert first == second
            assert first.reader == reader.name
            assert first.predicate == predicate.value
            assert first.case_id == case.id
            assert first.attack == case.attack.value


def test_summarize_flip_cost_is_reproducible() -> None:
    cases = generate_marketing_suite(1)
    first = summarize_flip_cost(cases, READER_LADDER[2], max_budget=8)
    second = summarize_flip_cost(cases, READER_LADDER[2], max_budget=8)
    assert first == second
    assert first.by_attack == second.by_attack
    assert first.n == len(cases)


def test_summarize_flip_cost_matches_independent_aggregation() -> None:
    cases = generate_marketing_suite()
    reader = READER_LADDER[2]
    summary = summarize_flip_cost(cases, reader, max_budget=LADDER_BUDGET)
    expected = _aggregate(_ladder_grid()[("choice", reader.name)])
    assert (
        summary.mean_flip_cost,
        summary.already_flipped_rate,
        summary.unflippable_rate,
    ) == expected


def test_summarize_flip_cost_rejects_empty_case_set() -> None:
    with pytest.raises(ValueError):
        summarize_flip_cost((), READER_LADDER[0])


# --- 2. exact minimality --------------------------------------------------------


@pytest.mark.parametrize(
    ("attack", "rung", "predicate"),
    [
        (MarketingAttack.MANUFACTURED_CONSENSUS, 4, FlipPredicate.CHOICE),
        (MarketingAttack.PLAIN_FALSE, 3, FlipPredicate.AUDIT),
        (MarketingAttack.CIRCULAR_CITATION, 2, FlipPredicate.PROVENANCE),
    ],
)
def test_flip_cost_equals_independent_brute_force_minimum(
    attack: MarketingAttack, rung: int, predicate: FlipPredicate
) -> None:
    case = make_marketing_case(0, attack, target_side=Side.B)
    reader = READER_LADDER[rung]
    result = flip_cost(case, reader, predicate=predicate, max_budget=8)
    assert result.cost == _brute_force_minimum(case, reader, predicate, 8)


def test_flip_cost_returns_none_when_no_plan_fits_the_cap() -> None:
    case = make_marketing_case(0, MarketingAttack.MANUFACTURED_CONSENSUS, target_side=Side.B)
    result = flip_cost(case, TOP_RUNG, predicate=FlipPredicate.CHOICE, max_budget=5)
    assert result.cost is None
    assert result.flipped is False
    assert result.plan == "none within budget"
    assert _brute_force_minimum(case, TOP_RUNG, FlipPredicate.CHOICE, 5) is None


# --- 3. enumerate_plans ---------------------------------------------------------


@settings(max_examples=25, deadline=None)
@given(st.integers(min_value=0, max_value=12))
def test_enumerate_plans_is_ordered_bounded_complete_and_unique(budget: int) -> None:
    plans = enumerate_plans(budget)
    costs = [plan.cost for plan in plans]
    assert costs == sorted(costs)
    assert all(cost <= budget for cost in costs)
    assert len(set(plans)) == len(plans)

    ranges = [range(budget // price + 1) for price in EXPECTED_PRICES.values()]
    expected = {
        counts
        for counts in itertools.product(*ranges)
        if sum(n * p for n, p in zip(counts, EXPECTED_PRICES.values(), strict=True)) <= budget
    }
    assert {tuple(plan.as_counts().values()) for plan in plans} == expected


def test_enumerate_plans_zero_budget_is_exactly_the_empty_plan() -> None:
    assert enumerate_plans(0) == (AttackerPlan(),)
    assert enumerate_plans(0)[0].is_empty


def test_enumerate_plans_rejects_negative_budget() -> None:
    with pytest.raises(ValueError):
        enumerate_plans(-1)


# --- 4. AttackerPlan ------------------------------------------------------------


def test_action_cost_table_matches_the_preregistered_prices() -> None:
    assert {action.value: cost for action, cost in ACTION_COSTS.items()} == EXPECTED_PRICES
    assert set(ACTION_COSTS) == set(AttackerAction)


@settings(max_examples=50, deadline=None)
@given(
    st.integers(min_value=0, max_value=4),
    st.integers(min_value=0, max_value=4),
    st.integers(min_value=0, max_value=4),
    st.integers(min_value=0, max_value=4),
    st.integers(min_value=0, max_value=4),
)
def test_plan_cost_is_the_priced_sum_of_its_actions(
    echo: int, seo: int, launder: int, bury: int, forge: int
) -> None:
    plan = AttackerPlan(echo, seo, launder, bury, forge)
    assert plan.cost == echo + seo + 3 * launder + 5 * bury + 8 * forge
    assert plan.cost == sum(
        EXPECTED_PRICES[name] * n for name, n in plan.as_counts().items()
    )
    assert plan.is_empty is (plan.cost == 0)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"echo": -1},
        {"seo_boost": -1},
        {"launder": -2},
        {"bury_lab": -1},
        {"forge_measurement": -1},
    ],
)
def test_negative_action_counts_are_rejected(kwargs: dict[str, int]) -> None:
    with pytest.raises(ValueError):
        AttackerPlan(**kwargs)


def test_describe_round_trips_the_action_names() -> None:
    assert AttackerPlan().describe() == "no action"
    plan = AttackerPlan(echo=3, seo_boost=1, launder=0, bury_lab=2, forge_measurement=1)
    described = plan.describe()
    assert described == "3xecho + 1xseo_boost + 2xbury_lab + 1xforge_measurement"
    recovered = {}
    for part in described.split(" + "):
        count, name = part.split("x", 1)
        assert name in EXPECTED_PRICES
        recovered[name] = int(count)
    assert recovered == {name: n for name, n in plan.as_counts().items() if n}


# --- 5. apply_plan never touches product truth ----------------------------------


def test_apply_plan_leaves_product_truth_and_the_original_case_untouched() -> None:
    case = make_marketing_case(2, MarketingAttack.FULL_STACK, target_side=Side.A)
    original_pages = case.pages
    pages_snapshot = tuple(original_pages)
    plan = AttackerPlan(echo=2, seo_boost=1, launder=1, bury_lab=1, forge_measurement=1)
    attacked = apply_plan(case, plan)

    assert attacked.products == case.products
    assert attacked.correct_side is case.correct_side
    assert attacked.target_side is case.target_side
    assert attacked.requirement_latency_ms == case.requirement_latency_ms
    assert attacked.requirement_budget_usd == case.requirement_budget_usd
    assert attacked.id == case.id
    assert attacked.attack is case.attack
    assert attacked.campaign_claim == case.campaign_claim

    # The attacker owns the information ecosystem and nothing else.
    assert attacked.pages is not case.pages
    assert case.pages is original_pages
    assert case.pages == pages_snapshot
    assert len(attacked.pages) == len(case.pages) + 2 + 1 + 1
    assert {page.id for page in case.pages} < {page.id for page in attacked.pages}
    boosted = [p for p in attacked.pages if p.id == "vendor"][0]
    assert boosted is not [p for p in case.pages if p.id == "vendor"][0]


def test_apply_plan_of_the_empty_plan_is_an_equal_case() -> None:
    case = make_marketing_case(1, MarketingAttack.CIRCULAR_CITATION, target_side=Side.A)
    assert apply_plan(case, AttackerPlan()) == case


# --- 6. oracle-freedom ----------------------------------------------------------


def test_reader_ladder_answers_never_depend_on_correct_side() -> None:
    """No rung may consult the answer key.

    ``correct_side`` is a plain field, so swapping it alone is exactly the mutation
    that isolates it: the pages, the products, the requirements and the campaign claim
    are untouched, and only the labelled answer moves. The resulting case is
    deliberately incoherent as a benchmark item — that is the point, since any reader
    reading the label would answer differently while a reader reading the pages cannot.
    """

    from dataclasses import replace

    for case in generate_marketing_suite(2):
        swapped = replace(
            case, correct_side=Side.A if case.correct_side is Side.B else Side.B
        )
        assert swapped.correct_side is not case.correct_side
        for reader in READER_LADDER:
            answer = reader.answer(case)
            assert reader.answer(swapped) == answer
            assert reader.read(swapped) == reader.read(case)
            for predicate in FlipPredicate:
                assert is_flipped(case, answer, predicate) == is_flipped(
                    swapped, answer, predicate
                )
            # Non-vacuity: the swapped field really is load-bearing for scoring, so
            # the invariance above is a property of the reader, not of the mutation.
            assert (
                score_marketing(case, answer).choice_correct
                is not score_marketing(swapped, answer).choice_correct
            )


def test_base_rung_is_fallible_so_oracle_freedom_is_not_trivial() -> None:
    """If a rung were already perfect, invariance under a swapped label would be free."""

    cases = generate_marketing_suite(2)
    base = READER_LADDER[0]
    wrong = sum(base.answer(case).choice is not case.correct_side for case in cases)
    assert 0 < wrong < len(cases)


def test_flip_cost_result_is_independent_of_correct_side() -> None:
    from dataclasses import replace

    case = make_marketing_case(0, MarketingAttack.BENCHMARK_LAUNDERING, target_side=Side.B)
    swapped = replace(case, correct_side=Side.A if case.correct_side is Side.B else Side.B)
    assert swapped.correct_side is not case.correct_side
    for predicate in FlipPredicate:
        base = flip_cost(case, READER_LADDER[3], predicate=predicate, max_budget=8)
        other = flip_cost(swapped, READER_LADDER[3], predicate=predicate, max_budget=8)
        assert base.cost == other.cost
        assert base.plan == other.plan


# --- 7. the pinned reader ladder ------------------------------------------------


@pytest.mark.parametrize("predicate", [p.value for p in FlipPredicate])
def test_ladder_pins_measured_flip_cost(predicate: str) -> None:
    grid = _ladder_grid()
    for rung, reader in enumerate(READER_LADDER):
        results = grid[(predicate, reader.name)]
        assert len(results) == LADDER_N
        mean_cost, already, unflippable = _aggregate(results)
        assert mean_cost == PINNED_MEAN[predicate][rung], (predicate, reader.name)
        assert already == PINNED_ALREADY_FLIPPED[predicate][rung], (predicate, reader.name)
        assert unflippable == PINNED_UNFLIPPABLE[predicate][rung], (predicate, reader.name)


def test_choice_flip_cost_is_monotone_non_decreasing_up_the_ladder() -> None:
    grid = _ladder_grid()
    means = [_aggregate(grid[("choice", reader.name)])[0] for reader in READER_LADDER]
    assert all(a <= b for a, b in zip(means, means[1:], strict=False))
    assert means[-1] > means[0], "the ladder must buy something measurable"
    already = [_aggregate(grid[("choice", reader.name)])[1] for reader in READER_LADDER]
    assert all(a >= b for a, b in zip(already, already[1:], strict=False))
    assert already[-1] == 0.0


def test_top_rung_choice_flip_cost_by_attack_is_pinned() -> None:
    by_attack: dict[str, set[int | None]] = {}
    for result in _ladder_grid()[("choice", TOP_RUNG.name)]:
        by_attack.setdefault(result.attack, set()).add(result.cost)
    assert all(len(costs) == 1 for costs in by_attack.values()), by_attack
    collapsed = {attack: costs.pop() for attack, costs in by_attack.items()}
    assert collapsed == PINNED_TOP_RUNG_CHOICE_BY_ATTACK


# --- 8. launder and bury_lab are never cost-optimal -----------------------------


def test_launder_and_bury_lab_are_never_cost_optimal() -> None:
    """A documented finding, pinned deliberately.

    Under the frozen price table no minimal plan ever buys ``launder`` or
    ``bury_lab``: ``echo`` defeats the same ranking pressure at cost 1, and the
    escalating top rung reads every page, so demoting the lab achieves nothing. If a
    future price change makes either action binding, this test must fail so the
    finding is revisited rather than silently invalidated.
    """

    selected = {result.plan for column in _ladder_grid().values() for result in column}
    assert selected == PINNED_SELECTED_PLANS
    for plan in selected:
        assert "launder" not in plan, plan
        assert "bury_lab" not in plan, plan


def test_echo_strictly_undercuts_launder_and_bury_lab_on_price() -> None:
    assert ACTION_COSTS[AttackerAction.ECHO] < ACTION_COSTS[AttackerAction.LAUNDER]
    assert ACTION_COSTS[AttackerAction.ECHO] < ACTION_COSTS[AttackerAction.BURY_LAB]


def test_bury_lab_is_inert_against_the_escalating_top_rung() -> None:
    for case in generate_marketing_suite(2):
        assert len(case.pages) < TOP_RUNG.max_reads
        buried = apply_plan(case, AttackerPlan(bury_lab=5))
        assert {page.id for page in TOP_RUNG.read(buried)} == {
            page.id for page in TOP_RUNG.read(case)
        }
        assert TOP_RUNG.answer(buried) == TOP_RUNG.answer(case)


# --- 9. flip predicates ---------------------------------------------------------


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        (MarketingAnswer(Side.B, False, 0), {"choice": True, "audit": False, "provenance": False}),
        (MarketingAnswer(Side.A, False, 0), {"choice": False, "audit": False, "provenance": False}),
        (MarketingAnswer(Side.A, True, 0), {"choice": False, "audit": True, "provenance": False}),
        (MarketingAnswer(Side.A, False, 3), {"choice": False, "audit": False, "provenance": True}),
        (MarketingAnswer(Side.B, True, 1), {"choice": True, "audit": True, "provenance": True}),
    ],
)
def test_is_flipped_per_predicate(answer: MarketingAnswer, expected: dict[str, bool]) -> None:
    case = make_marketing_case(0, MarketingAttack.PLAIN_FALSE, target_side=Side.B)
    assert case.target_side is Side.B
    for predicate in FlipPredicate:
        assert is_flipped(case, answer, predicate) is expected[predicate.value]


def test_is_flipped_choice_tracks_target_side_not_side_b() -> None:
    case = make_marketing_case(1, MarketingAttack.PLAIN_FALSE, target_side=Side.A)
    assert is_flipped(case, MarketingAnswer(Side.A, False, 0), FlipPredicate.CHOICE) is True
    assert is_flipped(case, MarketingAnswer(Side.B, False, 0), FlipPredicate.CHOICE) is False


@pytest.mark.parametrize(
    ("cost", "flipped", "already"),
    [(0, True, True), (1, True, False), (8, True, False), (None, False, False)],
)
def test_already_flipped_is_exactly_zero_cost(
    cost: int | None, flipped: bool, already: bool
) -> None:
    result = FlipCostResult(
        case_id="c", attack="plain_false", reader="r", predicate="choice",
        cost=cost, plan="p", max_budget=16,
    )
    assert result.flipped is flipped
    assert result.already_flipped is already


def test_already_flipped_rate_counts_exactly_the_zero_cost_cases() -> None:
    for column in _ladder_grid().values():
        zero = [r for r in column if r.cost == 0]
        assert [r for r in column if r.already_flipped] == zero
        assert all(r.plan == "no action" for r in zero)


# --- 10. ReaderPolicy validation ------------------------------------------------


@pytest.mark.parametrize("read_limit", [0, -1])
def test_read_limit_below_one_is_rejected(read_limit: int) -> None:
    with pytest.raises(ValueError):
        ReaderPolicy(name="bad", read_limit=read_limit)


def test_max_reads_below_read_limit_is_rejected() -> None:
    with pytest.raises(ValueError):
        ReaderPolicy(name="bad", read_limit=8, max_reads=7)
    assert ReaderPolicy(name="ok", read_limit=8, max_reads=8).max_reads == 8


def test_reader_reads_no_more_than_its_bound_and_dedupes() -> None:
    case = make_marketing_case(0, MarketingAttack.FULL_STACK, target_side=Side.B)
    reader = ReaderPolicy(name="narrow", stack=(PROVENANCE_LAYER,), read_limit=2)
    pages = reader.read(case)
    assert len(pages) == 2
    assert len({page.url for page in pages}) == 2
