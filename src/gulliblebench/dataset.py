from __future__ import annotations

from dataclasses import dataclass
from itertools import product

from .generator import make_counterfactual_pair
from .render import render_core
from .world import HiddenWorld, Side, VisibleWorld


@dataclass(frozen=True, slots=True)
class CoreCase:
    id: str
    hidden: HiddenWorld
    visible: VisibleWorld


def generate_core_suite(
    *,
    page_counts: tuple[int, ...] = (1, 2, 4, 8),
    reliabilities: tuple[float, ...] = (0.6, 0.75, 0.9),
    directions: tuple[Side, ...] = (Side.A, Side.B),
    provenance_modes: tuple[bool, ...] = (True,),
) -> tuple[CoreCase, ...]:
    cases: list[CoreCase] = []
    for n_pages, reliability, supports, explicit in product(
        page_counts, reliabilities, directions, provenance_modes
    ):
        echo, independent = make_counterfactual_pair(
            n_pages=n_pages,
            reliability=reliability,
            supports=supports,
            explicit_provenance=explicit,
        )
        for world in (echo, independent):
            mode = "explicit" if explicit else "implicit"
            case_id = (
                f"core-{mode}-n{n_pages}-r{int(round(reliability * 100)):02d}-"
                f"support{supports.value}-{world.metadata['condition']}"
            )
            hidden = HiddenWorld(
                id=case_id,
                prior_b=world.prior_b,
                truth=world.truth,
                evidence_origins=world.evidence_origins,
                pages=world.pages,
                provenance_edges=world.provenance_edges,
                metadata={**world.metadata, "provenance_mode": mode},
            )
            cases.append(CoreCase(case_id, hidden, render_core(hidden)))
    return tuple(cases)
