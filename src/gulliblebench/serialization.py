from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .dataset import CoreCase
from .oracle import bayes_posterior_b


def _json_default(value: object) -> object:
    if hasattr(value, "value"):
        return getattr(value, "value")
    raise TypeError(f"not JSON serializable: {type(value)!r}")


def export_core_jsonl(cases: tuple[CoreCase, ...], path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for case in cases:
            row = {
                "id": case.id,
                "prompt": case.visible.prompt,
                "target": {
                    "posterior_b": bayes_posterior_b(
                        case.hidden.prior_b, case.hidden.evidence_origins
                    ),
                    "independent_evidence_units": len(case.hidden.evidence_origins),
                    "truth": case.hidden.truth,
                },
                "metadata": case.hidden.metadata,
            }
            f.write(json.dumps(row, default=_json_default, sort_keys=True) + "\n")


def export_hidden_jsonl(cases: tuple[CoreCase, ...], path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for case in cases:
            f.write(json.dumps(asdict(case.hidden), default=_json_default, sort_keys=True) + "\n")
