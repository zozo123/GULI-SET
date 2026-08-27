from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from .baselines import naive_marketing_answer
from .evaluate import MarketingSummary, summarize_marketing
from .marketing import MarketingAttack, MarketingCase, make_marketing_case
from .marketing_scoring import MarketingAnswer, MarketingScore, score_marketing
from .world import Side

_DEFAULT_DEMO_RECIPE = """{
  "schema_version": 1,
  "world_index": 0,
  "target_side": "B",
  "attacks": [
    "plain_false",
    "authority_laundering",
    "manufactured_consensus",
    "circular_citation"
  ]
}"""
_LATENCY_MEASUREMENT = re.compile(r"([A-Za-z][A-Za-z0-9-]*) median latency = (\d+) ms")


@dataclass(frozen=True, slots=True)
class PolicyLayer:
    """One typed process improvement wrapped around the solver below it."""

    name: str
    role: str
    rationale: str


@dataclass(frozen=True, slots=True)
class FailureTrace:
    case_id: str
    attack: str
    choice_correct: bool
    claim_audit_correct: bool
    provenance_abs_error: int
    hard_constraint_violation: bool


@dataclass(frozen=True, slots=True)
class DepthSnapshot:
    depth: int
    stack: tuple[PolicyLayer, ...]
    summary: MarketingSummary
    traces: tuple[FailureTrace, ...]
    omega_context_items: int


@dataclass(frozen=True, slots=True)
class MetaDemoRun:
    cases: tuple[str, ...]
    snapshots: tuple[DepthSnapshot, ...]
    convergence_reason: str


PROVENANCE_LAYER = PolicyLayer(
    name="collapse_provenance",
    role="compression",
    rationale="Repeated pages with one root claim are one evidence unit.",
)
CONSTRAINT_LAYER = PolicyLayer(
    name="guard_constraints",
    role="routing",
    rationale="Route the decision through measured hard requirements before popularity.",
)
INDEPENDENCE_LAYER = PolicyLayer(
    name="verify_independence",
    role="verification",
    rationale="Accept support only when an independent measurement backs the campaign claim.",
)


class FrozenOmega:
    """A fixed, deterministic improver that reads a growing scored history.

    This is a compact demonstration of the Meta^n control pattern, not the paper's
    LLM code generator. Omega itself never changes; only its trace/code input grows.
    """

    def propose(
        self, history: tuple[DepthSnapshot, ...], stack: tuple[PolicyLayer, ...]
    ) -> PolicyLayer | None:
        latest = history[-1].summary
        installed = {layer.name for layer in stack}
        if latest.provenance_mae > 1.0 and PROVENANCE_LAYER.name not in installed:
            return PROVENANCE_LAYER
        if latest.hard_constraint_violation_rate > 0.0 and CONSTRAINT_LAYER.name not in installed:
            return CONSTRAINT_LAYER
        if (
            latest.claim_audit_accuracy < 1.0 or latest.provenance_mae > 0.0
        ) and INDEPENDENCE_LAYER.name not in installed:
            return INDEPENDENCE_LAYER
        return None


def load_demo_cases(path: str | Path | None = None) -> tuple[MarketingCase, ...]:
    """Expand the tiny public recipe into deterministic benchmark cases."""

    raw_recipe = _DEFAULT_DEMO_RECIPE if path is None else Path(path).read_text(encoding="utf-8")
    recipe = json.loads(raw_recipe)
    if not isinstance(recipe, dict):
        raise ValueError("demo recipe must be a JSON object")
    if recipe.get("schema_version") != 1:
        raise ValueError("demo recipe schema_version must be 1")
    try:
        world_index = recipe["world_index"]
        target_side = Side(recipe["target_side"])
        attacks = tuple(MarketingAttack(value) for value in recipe["attacks"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("invalid demo recipe") from exc
    if isinstance(world_index, bool) or not isinstance(world_index, int) or world_index < 0:
        raise ValueError("world_index must be a non-negative integer")
    if not attacks:
        raise ValueError("demo recipe must contain at least one attack")
    return tuple(
        make_marketing_case(world_index, attack, target_side=target_side) for attack in attacks
    )


def _measured_safe_choice(case: MarketingCase) -> Side | None:
    """Choose from measurements rendered in the visible pages, not hidden target labels."""

    measured_latency: dict[str, int] = {}
    for page in case.pages:
        for product_name, latency in _LATENCY_MEASUREMENT.findall(page.text):
            measured_latency[product_name] = int(latency)
    safe = [
        product.side
        for product in case.products
        if measured_latency.get(product.name, case.requirement_latency_ms + 1)
        <= case.requirement_latency_ms
        and product.monthly_usd <= case.requirement_budget_usd
        and product.encrypted
    ]
    return safe[0] if len(safe) == 1 else None


def solve_with_stack(
    case: MarketingCase,
    stack: tuple[PolicyLayer, ...],
    *,
    base: MarketingAnswer | None = None,
) -> MarketingAnswer:
    """Run a base solver through every installed layer.

    ``base`` defaults to the deliberately gullible page counter used by the Meta demo.
    The Flip Cost reader ladder passes its own bounded-attention base instead, so the
    same audited layer semantics serve both tracks.
    """

    answer = naive_marketing_answer(case) if base is None else base
    for layer in stack:
        if layer.name == PROVENANCE_LAYER.name:
            if answer.campaign_claim_supported:
                roots = {page.root_origin for page in case.pages if page.supports_campaign_claim}
                answer = replace(answer, independent_supporting_origins=len(roots))
        elif layer.name == CONSTRAINT_LAYER.name:
            safe_choice = _measured_safe_choice(case)
            if safe_choice is not None:
                answer = replace(answer, choice=safe_choice)
        elif layer.name == INDEPENDENCE_LAYER.name:
            roots = {
                page.root_origin
                for page in case.pages
                if page.supports_campaign_claim and page.independent_measurement
            }
            answer = replace(
                answer,
                campaign_claim_supported=bool(roots),
                independent_supporting_origins=len(roots),
            )
        else:
            raise ValueError(f"unknown policy layer: {layer.name}")
    return answer


def _failure_trace(case: MarketingCase, score: MarketingScore) -> FailureTrace:
    return FailureTrace(
        case_id=case.id,
        attack=case.attack.value,
        choice_correct=score.choice_correct,
        claim_audit_correct=score.claim_audit_correct,
        provenance_abs_error=score.provenance_abs_error,
        hard_constraint_violation=score.hard_constraint_violation,
    )


def run_meta_demo(
    cases: tuple[MarketingCase, ...], *, max_depth: int = 6, omega: FrozenOmega | None = None
) -> MetaDemoRun:
    """Build layers until the frozen improver converges or ``max_depth`` is reached."""

    if max_depth < 0:
        raise ValueError("max_depth must be non-negative")
    if not cases:
        raise ValueError("at least one demo case is required")
    improver = omega or FrozenOmega()
    stack: tuple[PolicyLayer, ...] = ()
    history: tuple[DepthSnapshot, ...] = ()
    reason = f"maximum depth {max_depth} reached"

    for depth in range(max_depth + 1):
        answers = {case.id: solve_with_stack(case, stack) for case in cases}
        summary = summarize_marketing(cases, answers)
        traces = tuple(
            _failure_trace(case, score_marketing(case, answers[case.id])) for case in cases
        )
        context_items = sum(len(snapshot.traces) for snapshot in history) + len(stack) + len(traces)
        snapshot = DepthSnapshot(depth, stack, summary, traces, context_items)
        history += (snapshot,)

        layer = improver.propose(history, stack)
        if layer is None:
            reason = (
                "no scored failures remain"
                if summary.strict_pass_rate == 1.0
                else "Omega converged"
            )
            break
        if depth == max_depth:
            break
        stack += (layer,)

    return MetaDemoRun(tuple(case.id for case in cases), history, reason)


def meta_demo_to_dict(run: MetaDemoRun) -> dict[str, object]:
    return {
        "cases": list(run.cases),
        "convergence_reason": run.convergence_reason,
        "snapshots": [
            {
                "depth": snapshot.depth,
                "stack": [asdict(layer) for layer in snapshot.stack],
                "summary": asdict(snapshot.summary),
                "omega_context_items": snapshot.omega_context_items,
                "traces": [asdict(trace) for trace in snapshot.traces],
            }
            for snapshot in run.snapshots
        ],
    }


def render_meta_demo(run: MetaDemoRun) -> str:
    lines = [
        "GULI-SET // META HARNESS",
        f"{len(run.cases)} tasks · fixed Omega · deterministic · zero API keys",
        "",
        "depth  stack                                      strict  audit   safe  prov MAE  Omega input",
        "-----  -----------------------------------------  ------  ------  -----  --------  -----------",
    ]
    for snapshot in run.snapshots:
        stack = "base:page_counter" if not snapshot.stack else f"+ {snapshot.stack[-1].name}"
        summary = snapshot.summary
        lines.append(
            f"{snapshot.depth:>5}  {stack:<41}  "
            f"{summary.strict_pass_rate:>5.0%}  "
            f"{summary.claim_audit_accuracy:>5.0%}  "
            f"{1.0 - summary.hard_constraint_violation_rate:>4.0%}  "
            f"{summary.provenance_mae:>8.3f}  "
            f"{snapshot.omega_context_items:>11}"
        )
    roles = " -> ".join(layer.role for layer in run.snapshots[-1].stack) or "none"
    lines.extend(("", f"emergent roles: {roles}", f"converged: {run.convergence_reason}"))
    return "\n".join(lines)
