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
from .scoring import ParsedAnswer, score_core


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
