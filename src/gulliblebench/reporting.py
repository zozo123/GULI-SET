from __future__ import annotations

import json
from pathlib import Path


def write_baseline_markdown(results: dict[str, dict[str, object]], path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GullibleBench baseline results",
        "",
        "These deterministic baselines validate metric direction and dynamic range.",
        "",
        "| Baseline | Core strict pass | Core posterior MAE | Marketing strict pass | Hard-constraint violations |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, tracks in results.items():
        c = tracks["core"]
        m = tracks["marketing"]
        lines.append(
            f"| {name} | {100 * c['strict_pass_rate']:.1f}% | {c['posterior_mae']:.4f} | "
            f"{100 * m['strict_pass_rate']:.1f}% | {100 * m['hard_constraint_violation_rate']:.1f}% |"
        )
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def dump_json(data: object, path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
