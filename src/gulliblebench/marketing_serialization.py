from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .marketing import MarketingCase, render_marketing_prompt


def _default(value: object) -> object:
    if hasattr(value, "value"):
        return getattr(value, "value")
    raise TypeError(type(value).__name__)


def export_marketing_jsonl(
    cases: tuple[MarketingCase, ...],
    path: str | Path,
    *,
    hidden: bool = False,
    defensive: bool = False,
) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for case in cases:
            if hidden:
                row = asdict(case)
            else:
                row = {
                    "id": case.id,
                    "prompt": render_marketing_prompt(case, defensive=defensive),
                    "metadata": {
                        "attack": case.attack,
                        "target_side": case.target_side,
                        "defensive_prompt": defensive,
                    },
                    "target": {
                        "choice": case.correct_side,
                        "campaign_claim_supported": False,
                        "independent_supporting_origins": 0,
                    },
                }
            f.write(json.dumps(row, default=_default, sort_keys=True) + "\n")


def export_agent_jsonl(cases: tuple[MarketingCase, ...], path: str | Path) -> None:
    from .marketing import render_agent_prompt

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for case in cases:
            row = {
                "id": case.id,
                "prompt": render_agent_prompt(case),
                "metadata": {"attack": case.attack, "target_side": case.target_side},
                "target": {
                    "choice": case.correct_side,
                    "campaign_claim_supported": False,
                    "independent_supporting_origins": 0,
                },
            }
            f.write(json.dumps(row, default=_default, sort_keys=True) + "\n")
