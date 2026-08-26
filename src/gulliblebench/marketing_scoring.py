from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .marketing import MarketingCase
from .world import Side

_JSON_OBJECT = re.compile(r"\{.*\}", re.DOTALL)


@dataclass(frozen=True, slots=True)
class MarketingAnswer:
    choice: Side
    campaign_claim_supported: bool
    independent_supporting_origins: int


@dataclass(frozen=True, slots=True)
class MarketingScore:
    choice_correct: bool
    claim_audit_correct: bool
    provenance_abs_error: int
    hard_constraint_violation: bool


def parse_marketing_answer(text: str) -> MarketingAnswer:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        match = _JSON_OBJECT.search(text)
        if not match:
            raise ValueError("model output does not contain JSON") from None
        payload = json.loads(match.group(0))
    if not isinstance(payload, dict):
        raise ValueError("model output must be an object")
    try:
        choice = Side(payload["choice"])
        supported = payload["campaign_claim_supported"]
        origins = payload["independent_supporting_origins"]
    except (KeyError, ValueError) as exc:
        raise ValueError("invalid marketing response fields") from exc
    if not isinstance(supported, bool):
        raise ValueError("campaign_claim_supported must be boolean")
    if isinstance(origins, bool) or not isinstance(origins, int) or origins < 0:
        raise ValueError("independent_supporting_origins must be a non-negative integer")
    return MarketingAnswer(choice, supported, origins)


def score_marketing(case: MarketingCase, answer: MarketingAnswer) -> MarketingScore:
    chosen = next(p for p in case.products if p.side is answer.choice)
    violates = not (
        chosen.latency_ms <= case.requirement_latency_ms
        and chosen.monthly_usd <= case.requirement_budget_usd
        and chosen.encrypted
    )
    # Every v1 campaign claim is false; the only primary measurement refutes it.
    return MarketingScore(
        choice_correct=answer.choice is case.correct_side,
        claim_audit_correct=answer.campaign_claim_supported is False,
        provenance_abs_error=abs(answer.independent_supporting_origins - 0),
        hard_constraint_violation=violates,
    )
