from __future__ import annotations

import json
import re

from .scoring import ParsedAnswer
from .world import Side

_JSON_OBJECT = re.compile(r"\{.*\}", re.DOTALL)


def parse_answer(text: str) -> ParsedAnswer:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        match = _JSON_OBJECT.search(text)
        if match is None:
            raise ValueError("model output does not contain a JSON object") from None
        try:
            payload = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise ValueError("model output contains invalid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("model output must be a JSON object")
    required = {"probability_b", "independent_evidence_units", "choice"}
    missing = required - payload.keys()
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")
    p, units, choice = (
        payload["probability_b"],
        payload["independent_evidence_units"],
        payload["choice"],
    )
    if isinstance(p, bool) or not isinstance(p, (int, float)):
        raise ValueError("probability_b must be numeric")
    if isinstance(units, bool) or not isinstance(units, int):
        raise ValueError("independent_evidence_units must be an integer")
    try:
        side = Side(choice)
    except ValueError as exc:
        raise ValueError("choice must be 'A' or 'B'") from exc
    return ParsedAnswer(float(p), units, side)
