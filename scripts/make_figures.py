from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt

from gulliblebench.baselines import naive_marketing_answer
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
