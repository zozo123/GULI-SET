from __future__ import annotations

from dataclasses import dataclass

from .oracle import logit


@dataclass(frozen=True, slots=True)
class PairMetrics:
    echo_inflation_log_odds: float
    independence_response_log_odds: float
    separation: float


def paired_evidence_metrics(
    *,
    one_source_probability_b: float,
    echo_probability_b: float,
    independent_probability_b: float,
    support_is_b: bool,
) -> PairMetrics:
    orient = lambda p: p if support_is_b else 1.0 - p
    base = logit(orient(one_source_probability_b))
    echo = logit(orient(echo_probability_b))
    independent = logit(orient(independent_probability_b))
    echo_inflation = echo - base
    independence_response = independent - base
    return PairMetrics(
        echo_inflation, independence_response, independence_response - echo_inflation
    )
