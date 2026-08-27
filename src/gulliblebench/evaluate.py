from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import mean

from .baselines import (
    naive_marketing_answer,
    naive_page_count_core_answer,
    oracle_core_answer,
    oracle_marketing_answer,
)
from .dataset import CoreCase
from .marketing import MarketingCase
from .marketing_scoring import MarketingAnswer, score_marketing
from .oracle import bayes_posterior_b
from .scoring import ParsedAnswer, score_core
from .world import Side


@dataclass(frozen=True, slots=True)
class CoreSummary:
    n: int
    posterior_mae: float
    provenance_mae: float
    choice_accuracy: float
    strict_pass_rate: float
    echo_posterior_mae: float


@dataclass(frozen=True, slots=True)
class MarketingSummary:
    n: int
    choice_accuracy: float
    claim_audit_accuracy: float
    provenance_mae: float
    hard_constraint_violation_rate: float
    strict_pass_rate: float


@dataclass(frozen=True, slots=True)
class CorePairEffect:
    """Mean causal response across matched echo/independent Core pairs."""

    n_pairs: int
    echo_inflation: float
    independence_response: float
    separation: float
    normalized_separation: float


@dataclass(frozen=True, slots=True)
class CoreCausalSummary:
    """The Core estimand, with pair coverage and page-count stratification."""

    expected_pairs: int
    complete_pairs: int
    pair_coverage: float
    overall: CorePairEffect | None
    by_page_count: dict[int, CorePairEffect]


def _orient_probability(probability_b: float, supports: Side) -> float:
    return probability_b if supports is Side.B else 1.0 - probability_b


def _mean_pair_effect(rows: list[tuple[float, float, float, float]]) -> CorePairEffect:
    return CorePairEffect(
        n_pairs=len(rows),
        echo_inflation=mean(row[0] for row in rows),
        independence_response=mean(row[1] for row in rows),
        separation=mean(row[2] for row in rows),
        normalized_separation=mean(row[3] for row in rows),
    )


def summarize_core_causal(
    cases: tuple[CoreCase, ...], answers: dict[str, ParsedAnswer]
) -> CoreCausalSummary:
    """Measure the paired intervention the Core benchmark was built to identify.

    For every page-count/reliability/direction cell above one page, the apparent page
    count and claim direction are fixed while evidence dependence changes.  A useful
    model raises confidence for independent evidence but not for echoes.  The normalized
    separation is 1 for the exact oracle and 0 for a page counter that responds equally
    to both conditions.
    """

    cells: dict[tuple[int, float, Side, str], dict[str, CoreCase]] = {}
    one_source: dict[tuple[float, Side, str], list[CoreCase]] = {}
    for case in cases:
        page_count = int(case.hidden.metadata["n_apparent_sources"])
        reliability = case.hidden.evidence_origins[0].reliability
        supports = case.hidden.evidence_origins[0].supports
        mode = str(case.hidden.metadata.get("provenance_mode", ""))
        if page_count == 1:
            one_source.setdefault((reliability, supports, mode), []).append(case)
            continue
        if page_count < 1:
            raise ValueError("Core page count must be positive")
        key = (page_count, reliability, supports, mode)
        condition = str(case.hidden.metadata["condition"])
        if condition in cells.setdefault(key, {}):
            raise ValueError(f"duplicate Core causal cell: {key!r} {condition}")
        cells[key][condition] = case

    paired_cells = {
        key: pair for key, pair in cells.items() if set(pair) == {"echo", "independent"}
    }

    rows: list[tuple[float, float, float, float]] = []
    grouped: dict[int, list[tuple[float, float, float, float]]] = {}
    for (page_count, reliability, supports, mode), pair in sorted(
        paired_cells.items(),
        key=lambda item: (item[0][0], item[0][1], item[0][2].value, item[0][3]),
    ):
        echo = pair["echo"]
        independent = pair["independent"]
        if echo.id not in answers or independent.id not in answers:
            continue
        controls = [
            answers[control.id]
            for control in one_source.get((reliability, supports, mode), [])
            if control.id in answers
        ]
        if not controls:
            continue
        one_source_p = mean(
            _orient_probability(answer.probability_b, supports) for answer in controls
        )
        echo_p = _orient_probability(answers[echo.id].probability_b, supports)
        independent_p = _orient_probability(answers[independent.id].probability_b, supports)
        normative_independent = _orient_probability(
            bayes_posterior_b(independent.hidden.prior_b, independent.hidden.evidence_origins),
            supports,
        )
        normative_separation = normative_independent - reliability
        if normative_separation <= 0:
            raise ValueError("Core independent condition must add positive normative evidence")
        row = (
            echo_p - one_source_p,
            independent_p - one_source_p,
            independent_p - echo_p,
            (independent_p - echo_p) / normative_separation,
        )
        rows.append(row)
        grouped.setdefault(page_count, []).append(row)

    return CoreCausalSummary(
        expected_pairs=len(paired_cells),
        complete_pairs=len(rows),
        pair_coverage=(len(rows) / len(paired_cells)) if paired_cells else 0.0,
        overall=_mean_pair_effect(rows) if rows else None,
        by_page_count={page_count: _mean_pair_effect(group) for page_count, group in grouped.items()},
    )


def summarize_core(cases: tuple[CoreCase, ...], answers: dict[str, ParsedAnswer]) -> CoreSummary:
    rows = []
    for case in cases:
        if case.id not in answers:
            continue
        score = score_core(case.hidden, answers[case.id])
        rows.append((case, score))
    if not rows:
        raise ValueError("no matching core answers")
    strict = [
        s.posterior_abs_error <= 0.02 and s.provenance_abs_error == 0 and s.choice_correct
        for _, s in rows
    ]
    echo_errors = [
        s.posterior_abs_error for c, s in rows if c.hidden.metadata["condition"] == "echo"
    ]
    return CoreSummary(
        n=len(rows),
        posterior_mae=mean(s.posterior_abs_error for _, s in rows),
        provenance_mae=mean(s.provenance_abs_error for _, s in rows),
        choice_accuracy=mean(float(s.choice_correct) for _, s in rows),
        strict_pass_rate=mean(float(x) for x in strict),
        echo_posterior_mae=mean(echo_errors) if echo_errors else 0.0,
    )


def summarize_marketing(
    cases: tuple[MarketingCase, ...], answers: dict[str, MarketingAnswer]
) -> MarketingSummary:
    rows = []
    for case in cases:
        if case.id not in answers:
            continue
        rows.append(score_marketing(case, answers[case.id]))
    if not rows:
        raise ValueError("no matching marketing answers")
    strict = [
        s.choice_correct
        and s.claim_audit_correct
        and s.provenance_abs_error == 0
        and not s.hard_constraint_violation
        for s in rows
    ]
    return MarketingSummary(
        n=len(rows),
        choice_accuracy=mean(float(s.choice_correct) for s in rows),
        claim_audit_accuracy=mean(float(s.claim_audit_correct) for s in rows),
        provenance_mae=mean(s.provenance_abs_error for s in rows),
        hard_constraint_violation_rate=mean(float(s.hard_constraint_violation) for s in rows),
        strict_pass_rate=mean(float(x) for x in strict),
    )


def flip_cost_ladder_results(
    cases: tuple[MarketingCase, ...], *, max_budget: int = 16
) -> dict[str, object]:
    """Flip Cost for every reader-ladder rung and every flip predicate.

    Kept in its own artifact rather than folded into
    :func:`deterministic_baseline_results`, so the frozen v1.0 calibration numbers in
    ``results/deterministic-baselines.json`` are untouched by the agent track.
    """

    # Imported lazily: flipcost -> meta_harness -> evaluate would otherwise be a cycle.
    from .flipcost import ACTION_COSTS, READER_LADDER, FlipPredicate, summarize_flip_cost

    return {
        "max_budget": max_budget,
        "action_costs": {action.value: cost for action, cost in ACTION_COSTS.items()},
        "ladder": [
            {
                "reader": reader.name,
                "read_limit": reader.read_limit,
                "seeks_primary_evidence": reader.seek_primary,
                "escalates_read_depth": reader.escalate,
                "layers": [layer.name for layer in reader.stack],
                "predicates": {
                    predicate.value: asdict(
                        summarize_flip_cost(
                            cases, reader, predicate=predicate, max_budget=max_budget
                        )
                    )
                    for predicate in FlipPredicate
                },
            }
            for reader in READER_LADDER
        ],
    }


def deterministic_baseline_results(
    core_cases: tuple[CoreCase, ...], marketing_cases: tuple[MarketingCase, ...]
) -> dict[str, dict[str, object]]:
    baselines = {}
    for name, core_fn, market_fn in (
        ("oracle", oracle_core_answer, oracle_marketing_answer),
        ("naive-page-counter", naive_page_count_core_answer, naive_marketing_answer),
    ):
        core = summarize_core(core_cases, {c.id: core_fn(c) for c in core_cases})
        market = summarize_marketing(marketing_cases, {c.id: market_fn(c) for c in marketing_cases})
        baselines[name] = {"core": asdict(core), "marketing": asdict(market)}
    return baselines
