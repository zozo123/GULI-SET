from __future__ import annotations

from dataclasses import replace

from .world import EdgeType, EvidenceOrigin, HiddenWorld, Page, ProvenanceEdge, Side


def _page_text(source: str, claim: Side, origin: str, reliability: float, explicit: bool) -> str:
    winner = f"Product {claim.value}"
    if explicit:
        return (
            f"{source} reports that {winner} is superior. This report is based on "
            f"evidence origin {origin}, which is correct {reliability:.0%} of the time."
        )
    return f"{source} reports that {winner} is superior."


def make_counterfactual_pair(
    *,
    n_pages: int = 4,
    reliability: float = 0.75,
    supports: Side = Side.B,
    prior_b: float = 0.5,
    explicit_provenance: bool = True,
) -> tuple[HiddenWorld, HiddenWorld]:
    if n_pages < 1:
        raise ValueError("n_pages must be positive")
    sources = tuple(f"Source-{i + 1}" for i in range(n_pages))

    origin = EvidenceOrigin("origin-1", supports, reliability)
    echo_pages = tuple(
        Page(
            id=f"page-{i + 1}",
            title=f"Report {i + 1}",
            text=_page_text(source, supports, origin.id, reliability, explicit_provenance),
            apparent_source=source,
            evidence_origin_id=origin.id,
            cites=(origin.id,),
            url=f"https://source-{i + 1}.test/report",
        )
        for i, source in enumerate(sources)
    )
    echo = HiddenWorld(
        id="echo",
        prior_b=prior_b,
        truth=supports,
        evidence_origins=(origin,),
        pages=echo_pages,
        provenance_edges=tuple(ProvenanceEdge(p.id, origin.id, EdgeType.CITES) for p in echo_pages),
        metadata={"condition": "echo", "n_apparent_sources": n_pages, "n_origins": 1},
    )

    origins = tuple(
        EvidenceOrigin(f"origin-{i + 1}", supports, reliability) for i in range(n_pages)
    )
    independent_pages = tuple(
        replace(
            echo_pages[i],
            text=_page_text(sources[i], supports, origins[i].id, reliability, explicit_provenance),
            evidence_origin_id=origins[i].id,
            cites=(origins[i].id,),
        )
        for i in range(n_pages)
    )
    independent = HiddenWorld(
        id="independent",
        prior_b=prior_b,
        truth=supports,
        evidence_origins=origins,
        pages=independent_pages,
        provenance_edges=tuple(
            ProvenanceEdge(p.id, p.evidence_origin_id, EdgeType.INDEPENDENT_MEASUREMENT)
            for p in independent_pages
        ),
        metadata={"condition": "independent", "n_apparent_sources": n_pages, "n_origins": n_pages},
    )
    return echo, independent
