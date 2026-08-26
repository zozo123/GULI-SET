from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Side(str, Enum):
    A = "A"
    B = "B"


class EdgeType(str, Enum):
    CITES = "cites"
    COPIES = "copies"
    PARAPHRASES = "paraphrases"
    INDEPENDENT_MEASUREMENT = "independent_measurement"
    FUNDED_BY = "funded_by"
    OWNED_BY = "owned_by"
    AFFILIATE_OF = "affiliate_of"


@dataclass(frozen=True, slots=True)
class EvidenceOrigin:
    id: str
    supports: Side
    reliability: float

    def __post_init__(self) -> None:
        if not 0.5 < self.reliability < 1.0:
            raise ValueError("reliability must be strictly between 0.5 and 1.0")


@dataclass(frozen=True, slots=True)
class ProvenanceEdge:
    source: str
    target: str
    kind: EdgeType


@dataclass(frozen=True, slots=True)
class Page:
    id: str
    title: str
    text: str
    apparent_source: str
    evidence_origin_id: str
    cites: tuple[str, ...] = ()
    url: str = ""
    owner: str = ""
    sponsored: bool = False
    search_boost: float = 0.0


@dataclass(frozen=True, slots=True)
class HiddenWorld:
    id: str
    prior_b: float
    truth: Side
    evidence_origins: tuple[EvidenceOrigin, ...]
    pages: tuple[Page, ...]
    provenance_edges: tuple[ProvenanceEdge, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 < self.prior_b < 1.0:
            raise ValueError("prior_b must be strictly between 0 and 1")
        origin_ids = {o.id for o in self.evidence_origins}
        if len(origin_ids) != len(self.evidence_origins):
            raise ValueError("evidence origin ids must be unique")
        for page in self.pages:
            if page.evidence_origin_id not in origin_ids:
                raise ValueError(f"page {page.id} references unknown origin")


@dataclass(frozen=True, slots=True)
class VisibleWorld:
    id: str
    prompt: str
    pages: tuple[Page, ...]
