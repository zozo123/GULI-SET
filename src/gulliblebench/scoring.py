from __future__ import annotations

from dataclasses import dataclass

from .oracle import bayes_posterior_b
from .world import HiddenWorld, Side


@dataclass(frozen=True, slots=True)
class ParsedAnswer:
    probability_b: float
    independent_evidence_units: int
    choice: Side

    def __post_init__(self) -> None:
        if not 0.0 <= self.probability_b <= 1.0:
            raise ValueError("probability_b must be in [0, 1]")
        if self.independent_evidence_units < 0:
            raise ValueError("independent_evidence_units must be non-negative")


@dataclass(frozen=True, slots=True)
class CoreScore:
    posterior_abs_error: float
    brier_truth: float
    provenance_abs_error: int
    choice_correct: bool


def score_core(world: HiddenWorld, answer: ParsedAnswer) -> CoreScore:
    posterior = bayes_posterior_b(world.prior_b, world.evidence_origins)
    truth_b = float(world.truth is Side.B)
    return CoreScore(
        posterior_abs_error=abs(answer.probability_b - posterior),
        brier_truth=(answer.probability_b - truth_b) ** 2,
        provenance_abs_error=abs(answer.independent_evidence_units - len(world.evidence_origins)),
        choice_correct=answer.choice is world.truth,
    )
