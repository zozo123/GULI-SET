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


def render_flip_cost_ladder(results: dict[str, object], *, predicate: str | None = None) -> str:
    """Terminal view of the Flip Cost ladder, in the same shape as the Meta-harness demo."""

    ladder = results["ladder"]
    assert isinstance(ladder, list)
    if not ladder:
        raise ValueError("flip cost results contain no reader ladder")
    predicates = [p for p in ladder[0]["predicates"] if predicate in (None, p)]
    if not predicates:
        raise ValueError(f"unknown flip predicate: {predicate}")
    n = ladder[0]["predicates"][predicates[0]]["n"]
    lines = [
        "GULI-SET // FLIP COST",
        f"{n} agent cases · budget cap {results['max_budget']} · exact · zero API keys",
        "",
        "predicate    reader                    mean  median  min  zero-cost  unflippable",
        "-----------  ----------------------  ------  ------  ---  ---------  -----------",
    ]
    for name in predicates:
        for rung in ladder:
            summary = rung["predicates"][name]
            mean_cost = summary["mean_flip_cost"]
            median = summary["median_flip_cost"]
            minimum = summary["min_flip_cost"]
            lines.append(
                f"{name:<11}  {rung['reader']:<22}  "
                f"{'n/a' if mean_cost is None else f'{mean_cost:.2f}':>6}  "
                f"{'n/a' if median is None else f'{median:.1f}':>6}  "
                f"{'n/a' if minimum is None else minimum:>3}  "
                f"{summary['already_flipped_rate']:>9.0%}  "
                f"{summary['unflippable_rate']:>11.0%}"
            )
        lines.append("")
    lines.append("zero-cost = reader already wrong before the attacker spends anything")
    lines.append("unflippable = no plan within the cap flipped it, not a proof of safety")
    return "\n".join(lines)


def write_flip_cost_markdown(results: dict[str, object], path: str | Path) -> None:
    """Render the Flip Cost ladder as one table per flip predicate."""

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    ladder = results["ladder"]
    assert isinstance(ladder, list)
    costs = results["action_costs"]
    assert isinstance(costs, dict)
    lines = [
        "# GullibleBench Flip Cost",
        "",
        "Minimum attacker budget that flips a deterministic bounded-attention reader on the",
        "synthetic-web agent track. Flip Cost measures a defense, not a model.",
        "",
        f"Budget cap: {results['max_budget']}. "
        f"Price table: {', '.join(f'{k}={v}' for k, v in costs.items())}.",
        "",
        "`unflippable` means no plan within the cap flipped the reader, never that the reader is",
        "provably unflippable. Mean flip cost is taken over flippable cases only; censored cases",
        "are reported as `unflippable` rather than imputed at the cap.",
        "",
    ]
    predicates = list(ladder[0]["predicates"]) if ladder else []
    for predicate in predicates:
        lines.extend(
            (
                f"## Predicate: {predicate}",
                "",
                "| Reader | Layers | Mean flip cost | Median | Min | Zero-cost flips | Unflippable |",
                "|---|---|---:|---:|---:|---:|---:|",
            )
        )
        for rung in ladder:
            summary = rung["predicates"][predicate]
            layers = ", ".join(rung["layers"]) or "none"
            mean_cost = summary["mean_flip_cost"]
            median = summary["median_flip_cost"]
            minimum = summary["min_flip_cost"]
            lines.append(
                f"| `{rung['reader']}` | {layers} | "
                f"{'n/a' if mean_cost is None else f'{mean_cost:.3f}'} | "
                f"{'n/a' if median is None else f'{median:.1f}'} | "
                f"{'n/a' if minimum is None else minimum} | "
                f"{100 * summary['already_flipped_rate']:.1f}% | "
                f"{100 * summary['unflippable_rate']:.1f}% |"
            )
        lines.append("")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def dump_json(data: object, path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
