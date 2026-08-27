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


def parse_attacker_plan(spec: str | None):
    """Parse ``'echo=6,seo_boost=1'`` into an :class:`~gulliblebench.flipcost.AttackerPlan`."""

    from .flipcost import AttackerPlan

    if not spec:
        return AttackerPlan()
    counts: dict[str, int] = {}
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        name, _, raw = part.partition("=")
        if not _:
            raise ValueError(f"attacker plan entries must be name=count, got {part!r}")
        try:
            counts[name.strip()] = int(raw)
        except ValueError as exc:
            raise ValueError(f"attacker plan count must be an integer, got {raw!r}") from exc
    valid = set(AttackerPlan().as_counts())
    unknown = sorted(set(counts) - valid)
    if unknown:
        raise ValueError(f"unknown attacker actions {unknown}; valid actions are {sorted(valid)}")
    return AttackerPlan(**counts)


def render_web_query(
    *,
    case_id: str,
    action: str,
    query: str,
    limit: int = 5,
    attacker_plan: str | None = None,
) -> str:
    """Serve one ``search`` or ``open`` against the closed synthetic web, as plain text.

    This is the shell-facing form of :class:`~gulliblebench.synthetic_web.SyntheticWeb`, so a
    terminal agent can be evaluated on the agent track through the same closed world the
    deterministic reader ladder uses. Exactly like the Inspect ``open()`` tool, it returns
    only source, url, text, and citations: the hidden provenance annotations that the reader
    ladder consumes are never exposed here.
    """

    from .flipcost import apply_plan
    from .marketing import generate_marketing_suite
    from .synthetic_web import SyntheticWeb

    cases = {case.id: case for case in generate_marketing_suite()}
    if case_id not in cases:
        raise ValueError(f"unknown case id: {case_id}")
    case = apply_plan(cases[case_id], parse_attacker_plan(attacker_plan))
    web = SyntheticWeb(case)

    if action == "search":
        results = web.search(query, limit=max(1, min(limit, 50)))
        if not results:
            return "no results"
        return "\n".join(
            f"{i}. {r.source} | {r.title} | {r.url}" for i, r in enumerate(results, start=1)
        )
    page = web.open(query)
    cites = ", ".join(page.cites) if page.cites else "none"
    return f"Source: {page.source}\nURL: {page.url}\n{page.text}\nCites: {cites}"


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
        "predicate    reader                   clean    mean  restr  min  zero-cost  unflippable",
        "-----------  ----------------------  ------  ------  -----  ---  ---------  -----------",
    ]
    for name in predicates:
        for rung in ladder:
            summary = rung["predicates"][name]
            mean_cost = summary["mean_flip_cost"]
            minimum = summary["min_flip_cost"]
            lines.append(
                f"{name:<11}  {rung['reader']:<22}  "
                f"{summary['clean_accuracy']:>6.0%}  "
                f"{'n/a' if mean_cost is None else f'{mean_cost:.2f}':>6}  "
                f"{summary['restricted_mean_flip_cost']:>5.2f}  "
                f"{'n/a' if minimum is None else minimum:>3}  "
                f"{summary['already_flipped_rate']:>9.0%}  "
                f"{summary['unflippable_rate']:>11.0%}"
            )
        lines.append("")
    lines.extend(
        (
            "clean = unattacked accuracy. A high flip cost means nothing without it: a reader",
            "        that opens nothing and never believes the campaign is unflippable and useless.",
            "mean  = over flippable cases only, so it is blind to censoring. Never read it alone.",
            "restr = censored cases counted at the cap. Monotone, so use this to rank defenses.",
            "zero-cost = reader already wrong before the attacker spends anything",
            "unflippable = no plan within the cap flipped it, not a proof of safety",
        )
    )
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
        "provably unflippable.",
        "",
        "Read the three cost statistics together. `Mean` conditions on flippable cases and is",
        "therefore blind to censoring: a defense that turns censored cases into cheap flips has",
        "become strictly worse without moving it. `Restricted` counts censored cases at the cap and",
        "is monotone in defense strength, so it is the statistic to rank defenses by. `Clean` is",
        "unattacked accuracy, and without it a high flip cost is meaningless: a reader that opens",
        "nothing and never believes the campaign is unflippable and useless.",
        "",
    ]
    predicates = list(ladder[0]["predicates"]) if ladder else []
    for predicate in predicates:
        lines.extend(
            (
                f"## Predicate: {predicate}",
                "",
                "| Reader | Layers | Clean accuracy | Mean | Restricted mean | Min | "
                "Zero-cost flips | Unflippable |",
                "|---|---|---:|---:|---:|---:|---:|---:|",
            )
        )
        for rung in ladder:
            summary = rung["predicates"][predicate]
            layers = ", ".join(rung["layers"]) or "none"
            mean_cost = summary["mean_flip_cost"]
            minimum = summary["min_flip_cost"]
            lines.append(
                f"| `{rung['reader']}` | {layers} | "
                f"{100 * summary['clean_accuracy']:.1f}% | "
                f"{'n/a' if mean_cost is None else f'{mean_cost:.3f}'} | "
                f"{summary['restricted_mean_flip_cost']:.3f} | "
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
