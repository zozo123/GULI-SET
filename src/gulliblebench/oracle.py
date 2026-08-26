from __future__ import annotations

import math

from .world import EvidenceOrigin, Side


def logit(p: float) -> float:
    if not 0.0 < p < 1.0:
        raise ValueError("probability must be strictly between 0 and 1")
    return math.log(p / (1.0 - p))


def sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def bayes_log_odds_b(prior_b: float, origins: tuple[EvidenceOrigin, ...]) -> float:
    """Exact posterior log-odds for conditionally independent evidence origins."""
    if not 0.0 < prior_b < 1.0:
        raise ValueError("prior_b must be strictly between 0 and 1")
    out = logit(prior_b)
    seen: set[str] = set()
    for origin in origins:
        if origin.id in seen:
            raise ValueError(f"duplicate evidence origin id: {origin.id}")
        seen.add(origin.id)
        weight = math.log(origin.reliability / (1.0 - origin.reliability))
        out += weight if origin.supports is Side.B else -weight
    return out


def bayes_posterior_b(prior_b: float, origins: tuple[EvidenceOrigin, ...]) -> float:
    return sigmoid(bayes_log_odds_b(prior_b, origins))
