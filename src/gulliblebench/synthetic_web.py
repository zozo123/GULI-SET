from __future__ import annotations

import re
from dataclasses import dataclass

from .marketing import MarketingCase, MarketingPage

_TOKEN = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True, slots=True)
class SearchResult:
    url: str
    title: str
    source: str
    score: float


class SyntheticWeb:
    """Deterministic local search/open environment over one generated marketing world."""

    def __init__(self, case: MarketingCase):
        self.case = case
        self._by_url = {p.url: p for p in case.pages}

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return set(_TOKEN.findall(text.lower()))

    def search(self, query: str, *, limit: int = 5) -> tuple[SearchResult, ...]:
        q = self._tokens(query)
        ranked: list[SearchResult] = []
        for p in self.case.pages:
            body = self._tokens(f"{p.title} {p.text} {p.source}")
            overlap = len(q & body) / max(1, len(q))
            score = overlap + p.search_boost
            ranked.append(SearchResult(p.url, p.title, p.source, score))
        ranked.sort(key=lambda x: (-x.score, x.url))
        return tuple(ranked[:limit])

    def open(self, url: str) -> MarketingPage:
        try:
            return self._by_url[url]
        except KeyError as exc:
            raise KeyError(f"unknown synthetic URL: {url}") from exc
