from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt

from gulliblebench.baselines import naive_marketing_answer
from gulliblebench.flipcost import READER_LADDER, FlipPredicate, summarize_flip_cost
from gulliblebench.marketing import generate_marketing_suite
from gulliblebench.marketing_scoring import score_marketing
from gulliblebench.oracle import bayes_posterior_b
from gulliblebench.world import EvidenceOrigin, Side

OUT = Path("figures")
OUT.mkdir(exist_ok=True)

# Figure 1: normative correlation-neglect curve.
ns = [1, 2, 4, 8]
echo = []
independent = []
for n in ns:
    echo.append(bayes_posterior_b(0.5, (EvidenceOrigin("o", Side.B, 0.75),)))
    independent.append(
        bayes_posterior_b(0.5, tuple(EvidenceOrigin(f"o{i}", Side.B, 0.75) for i in range(n)))
    )
plt.figure(figsize=(6.4, 4.0))
plt.plot(ns, echo, marker="o", label="One origin echoed")
plt.plot(ns, independent, marker="o", label="Independent origins")
plt.xlabel("Apparent source count")
plt.ylabel("Normative P(B)")
plt.ylim(0.5, 1.01)
plt.xticks(ns)
plt.legend()
plt.tight_layout()
plt.savefig(OUT / "core_normative_curve.png", dpi=180)
plt.close()

# Figure 2: deterministic baseline strict-pass scorecard.
baselines = json.load(open("results/deterministic-baselines.json"))
labels = ["Oracle Core", "Naive Core", "Oracle Marketing", "Naive Marketing"]
values = [
    baselines["oracle"]["core"]["strict_pass_rate"] * 100,
    baselines["naive-page-counter"]["core"]["strict_pass_rate"] * 100,
    baselines["oracle"]["marketing"]["strict_pass_rate"] * 100,
    baselines["naive-page-counter"]["marketing"]["strict_pass_rate"] * 100,
]
plt.figure(figsize=(7.2, 4.0))
plt.bar(labels, values)
plt.ylabel("Strict pass rate (%)")
plt.ylim(0, 105)
plt.xticks(rotation=20, ha="right")
plt.tight_layout()
plt.savefig(OUT / "baseline_scorecard.png", dpi=180)
plt.close()

# Figure 3: naive marketing pass by attack.
by_attack = defaultdict(list)
for case in generate_marketing_suite():
    s = score_marketing(case, naive_marketing_answer(case))
    strict = s.choice_correct and s.claim_audit_correct and s.provenance_abs_error == 0 and not s.hard_constraint_violation
    by_attack[case.attack.value].append(float(strict))
attack_names = list(by_attack)
attack_values = [100 * sum(by_attack[a]) / len(by_attack[a]) for a in attack_names]
plt.figure(figsize=(9.0, 4.4))
plt.bar(attack_names, attack_values)
plt.ylabel("Naive strict pass rate (%)")
plt.ylim(0, 105)
plt.xticks(rotation=35, ha="right")
plt.tight_layout()
plt.savefig(OUT / "naive_marketing_by_attack.png", dpi=180)
plt.close()

# Figure 4: Flip Cost across the reader ladder. Three panels on predicate=choice cover
# attacker cost, free flips, and unattacked usefulness; the fourth panel shows on
# predicate=audit why the conditional mean must never be read on its own.
CHOICE_BUDGET = 16
suite = generate_marketing_suite()
choice_rungs = [
    summarize_flip_cost(suite, reader, predicate=FlipPredicate.CHOICE, max_budget=CHOICE_BUDGET)
    for reader in READER_LADDER
]
audit_rungs = [
    summarize_flip_cost(suite, reader, predicate=FlipPredicate.AUDIT, max_budget=CHOICE_BUDGET)
    for reader in READER_LADDER
]
rung_labels = [f"rung {i}\n{summary.reader}" for i, summary in enumerate(choice_rungs)]
xs = list(range(len(rung_labels)))
WIDTH = 0.38
left = [x - WIDTH / 2 for x in xs]
right = [x + WIDTH / 2 for x in xs]
COND_COLOR = "#3b6ea5"
REST_COLOR = "#9fbfdd"
ZERO_COLOR = "#a5533b"
CLEAN_COLOR = "#4a7c59"


def _conditional(summaries):
    """Mean over flippable cases; 0.0 stands in when every case is censored."""

    return [0.0 if s.mean_flip_cost is None else float(s.mean_flip_cost) for s in summaries]


def _label(axis, positions, values, fmt, pad):
    for x, value in zip(positions, values):
        axis.text(x, value + pad, fmt.format(value), ha="center", va="bottom", fontsize=8)


fig, axes = plt.subplots(2, 2, figsize=(12.4, 9.0), sharex=True)
(cost_ax, zero_ax), (clean_ax, censor_ax) = axes

# (a) attacker cost, both statistics side by side.
choice_cond = _conditional(choice_rungs)
choice_rest = [s.restricted_mean_flip_cost for s in choice_rungs]
cost_ax.bar(left, choice_cond, WIDTH, color=COND_COLOR, label="mean over flippable cases")
cost_ax.bar(
    right,
    choice_rest,
    WIDTH,
    color=REST_COLOR,
    label=f"restricted mean (censored cases counted at {CHOICE_BUDGET})",
)
_label(cost_ax, left, choice_cond, "{:.3g}", 0.2)
_label(cost_ax, right, choice_rest, "{:.3g}", 0.2)
cost_ax.set_title(
    "(a) Attacker budget needed to flip the choice — higher is a stronger defense",
    fontsize=10,
)
cost_ax.set_ylabel("Flip cost (budget units)")
cost_ax.set_ylim(0, max(choice_rest) * 1.35)
cost_ax.legend(fontsize=8, loc="upper left")
choice_censored = max(s.unflippable_rate for s in choice_rungs)
CENSOR_NOTE = (
    "no case is censored on this predicate,\nso the two statistics agree exactly"
    if choice_censored == 0
    else f"up to {100 * choice_censored:.0f}% of cases are censored at the cap,\n"
    "so only the restricted mean is safe to rank on"
)
cost_ax.text(
    0.03,
    0.45,
    CENSOR_NOTE,
    transform=cost_ax.transAxes,
    ha="left",
    va="center",
    fontsize=8,
    color="#444444",
)

# (b) flips the attacker gets without spending anything.
zero_rates = [100 * s.already_flipped_rate for s in choice_rungs]
zero_ax.bar(xs, zero_rates, 0.6, color=ZERO_COLOR)
_label(zero_ax, xs, zero_rates, "{:.0f}%", 1.5)
zero_ax.set_title(
    "(b) Cases already wrong at budget 0 — free flips survive four rungs", fontsize=10
)
zero_ax.set_ylabel("Zero-cost flips (% of 64 cases)")
zero_ax.set_ylim(0, 105)

# (c) usefulness when nobody is attacking.
clean_rates = [100 * s.clean_accuracy for s in choice_rungs]
clean_ax.bar(xs, clean_rates, 0.6, color=CLEAN_COLOR)
_label(clean_ax, xs, clean_rates, "{:.0f}%", 1.5)
clean_ax.set_title(
    "(c) Unattacked accuracy — a high flip cost only counts if this is high too", fontsize=10
)
clean_ax.set_ylabel("Clean accuracy (%)")
clean_ax.set_ylim(0, 105)

# (d) the censoring trap, on the predicate where it actually bites.
audit_cond = _conditional(audit_rungs)
audit_rest = [s.restricted_mean_flip_cost for s in audit_rungs]
censor_ax.bar(left, audit_cond, WIDTH, color=COND_COLOR, label="mean over flippable cases")
censor_ax.bar(right, audit_rest, WIDTH, color=REST_COLOR, label="restricted mean")
_label(censor_ax, left, audit_cond, "{:.3g}", 0.2)
_label(censor_ax, right, audit_rest, "{:.3g}", 0.2)
for x, target, summary in zip(right, audit_rest, audit_rungs):
    if summary.unflippable_rate:
        censor_ax.annotate(
            f"{100 * summary.unflippable_rate:.0f}% of cases not flippable\n"
            f"within {CHOICE_BUDGET}, counted at the cap here",
            xy=(x, target),
            xytext=(x - 1.3, max(audit_rest) * 1.32),
            ha="center",
            va="bottom",
            fontsize=8,
            color="#7a2f2f",
            arrowprops={"arrowstyle": "->", "color": "#7a2f2f", "linewidth": 0.8},
        )
TIE_NOTE = "the two statistics agree on every rung here"
for i in range(len(audit_rungs) - 1):
    if audit_cond[i] == audit_cond[i + 1] and audit_rest[i] != audit_rest[i + 1]:
        TIE_NOTE = (
            f"rungs {i} and {i + 1} tie at {audit_cond[i]:.3g} on that mean;\n"
            f"the restricted mean separates them, {audit_rest[i]:.3g} vs "
            f"{audit_rest[i + 1]:.3g}"
        )
        break
censor_ax.set_title(
    "(d) predicate=audit: why the flippable-case mean is never read alone\n" + TIE_NOTE,
    fontsize=10,
)
censor_ax.set_ylabel("Flip cost (budget units)")
censor_ax.set_ylim(0, max(audit_rest) * 1.50)
censor_ax.legend(fontsize=8, loc="center left")

for axis in (cost_ax, zero_ax, clean_ax, censor_ax):
    axis.set_axisbelow(True)
    axis.grid(axis="y", alpha=0.3)
for axis in (clean_ax, censor_ax):
    axis.set_xticks(xs)
    axis.set_xticklabels(rung_labels)
    axis.set_xlabel("Reader-ladder rung: each rung adds one Meta-harness policy layer")
    plt.setp(axis.get_xticklabels(), rotation=12, ha="right", fontsize=8)
fig.suptitle(
    "Flip Cost across the reader ladder: cost, free flips, and usefulness together\n"
    f"{len(suite)} marketing cases · budget cap {CHOICE_BUDGET} · panels (a)-(c) "
    "predicate=choice, panel (d) predicate=audit"
)
fig.align_ylabels(axes)
plt.tight_layout()
plt.savefig(OUT / "flip_cost_ladder.png", dpi=180)
plt.close()

# Figure 5: flip rate as a function of attacker budget, one line per rung. This is the
# fully identified form of the metric: every point is an observed fraction at that
# budget, with no imputation for censored cases.
budgets = list(range(CHOICE_BUDGET + 1))
curve_styles = [
    ("#c6d9ec", "-", "o", 2.6),
    ("#3b6ea5", "--", "s", 1.8),
    ("#f0c6a0", "-", "o", 2.6),
    ("#a5533b", "--", "s", 1.8),
    ("#2f5d3a", "-", "D", 2.0),
]
# Some rungs have identical curves. Each duplicate is drawn dashed over the solid
# curve it repeats, and the legend names the rung it repeats, so an exact overlap can
# never be mistaken for a missing line.
curve_notes = []
first_seen: dict[tuple[float, ...], int] = {}
for rung, summary in enumerate(choice_rungs):
    curve = tuple(summary.flip_rate_by_budget[b] for b in budgets)
    original = first_seen.setdefault(curve, rung)
    curve_notes.append("" if original == rung else f" (identical to rung {original})")
plt.figure(figsize=(8.6, 5.4))
for summary, label, note, (color, style, marker, lw) in zip(
    choice_rungs, rung_labels, curve_notes, curve_styles
):
    plt.plot(
        budgets,
        [summary.flip_rate_by_budget[b] for b in budgets],
        color=color,
        linestyle=style,
        marker=marker,
        markersize=4,
        linewidth=lw,
        label=label.replace("\n", " ") + note,
    )
plt.xlabel("Attacker budget (units from the frozen price table)")
plt.ylabel("Fraction of the 64 cases flipped at or below this budget")
plt.title(
    "Flip rate by attacker budget, per reader-ladder rung\n"
    f"predicate=choice · {len(suite)} marketing cases · budget cap {CHOICE_BUDGET}\n"
    "curves lower and further right are stronger defenses",
    fontsize=11,
)
plt.text(
    0.30,
    0.73,
    "Every point is an observed fraction at that budget:\n"
    "fully identified, nothing imputed for censored cases.",
    transform=plt.gca().transAxes,
    ha="left",
    va="center",
    fontsize=8,
    color="#444444",
)
plt.xticks(budgets)
plt.yticks([0.0, 0.25, 0.5, 0.75, 1.0])
plt.ylim(-0.04, 1.08)
plt.xlim(-0.4, CHOICE_BUDGET + 0.4)
plt.grid(alpha=0.3)
plt.gca().set_axisbelow(True)
plt.legend(fontsize=8, loc="lower right", title="Reader-ladder rung")
plt.tight_layout()
plt.savefig(OUT / "flip_cost_budget_curve.png", dpi=180)
plt.close()
