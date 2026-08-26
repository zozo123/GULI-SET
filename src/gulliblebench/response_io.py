from __future__ import annotations

import json
from pathlib import Path

from .dataset import CoreCase
from .evaluate import summarize_core, summarize_marketing
from .marketing import MarketingCase
from .marketing_scoring import MarketingAnswer, parse_marketing_answer
from .parsing import parse_answer
from .scoring import ParsedAnswer


def _answer_text(value: object) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value)


def load_response_rows(path: str | Path) -> dict[str, object]:
    rows: dict[str, object] = {}
    with Path(path).open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict) or "id" not in row or "answer" not in row:
                raise ValueError(f"line {line_no}: expected object with id and answer")
            ident = str(row["id"])
            if ident in rows:
                raise ValueError(f"duplicate response id: {ident}")
            rows[ident] = row["answer"]
    return rows


def score_core_response_file(cases: tuple[CoreCase, ...], path: str | Path):
    raw = load_response_rows(path)
    answers: dict[str, ParsedAnswer] = {
        ident: parse_answer(_answer_text(answer)) for ident, answer in raw.items()
    }
    return summarize_core(cases, answers)


def score_marketing_response_file(cases: tuple[MarketingCase, ...], path: str | Path):
    raw = load_response_rows(path)
    answers: dict[str, MarketingAnswer] = {
        ident: parse_marketing_answer(_answer_text(answer)) for ident, answer in raw.items()
    }
    return summarize_marketing(cases, answers)
