from __future__ import annotations

from .dataset import CoreCase
from .marketing import MarketingCase
from .marketing_scoring import MarketingAnswer
from .oracle import bayes_posterior_b
from .scoring import ParsedAnswer
from .world import EvidenceOrigin, Side


def oracle_core_answer(case: CoreCase) -> ParsedAnswer:
    p = bayes_posterior_b(case.hidden.prior_b, case.hidden.evidence_origins)
    return ParsedAnswer(p, len(case.hidden.evidence_origins), Side.B if p >= 0.5 else Side.A)


def naive_page_count_core_answer(case: CoreCase) -> ParsedAnswer:
    """Deliberately gullible baseline: treat every page as an independent observation."""
    pseudo = tuple(
        EvidenceOrigin(
            id=f"page-origin-{i}",
            supports=next(
                o.supports for o in case.hidden.evidence_origins if o.id == page.evidence_origin_id
            ),
            reliability=next(
                o.reliability
                for o in case.hidden.evidence_origins
                if o.id == page.evidence_origin_id
            ),
        )
        for i, page in enumerate(case.hidden.pages)
    )
    p = bayes_posterior_b(case.hidden.prior_b, pseudo)
    return ParsedAnswer(p, len(case.hidden.pages), Side.B if p >= 0.5 else Side.A)


def oracle_marketing_answer(case: MarketingCase) -> MarketingAnswer:
    return MarketingAnswer(case.correct_side, False, 0)


def naive_marketing_answer(case: MarketingCase) -> MarketingAnswer:
    """Deliberately gullible baseline: trust apparent campaign majority over the lab."""
    supporting_pages = sum(p.supports_campaign_claim for p in case.pages)
    refuting_pages = len(case.pages) - supporting_pages
    if supporting_pages > refuting_pages:
        return MarketingAnswer(case.target_side, True, supporting_pages)
    return MarketingAnswer(case.correct_side, False, 0)
