# GullibleBench: Epistemic Robustness to Manufactured Consensus

## Question

Can LLM agents distinguish many independent pieces of evidence from many webpages that all descend from one strategically produced claim?

## Method

Generate synthetic causal worlds with exact hidden truth, source reliability, provenance DAGs, user constraints, and deterministic marketing transformations. Compare matched worlds where visible evidence volume is similar but statistical independence differs. Extend the controlled Core experiment to synthetic product research with false marketing, authority/benchmark laundering, circular citation, manufactured consensus, and deterministic search ranking.

## Primary outcomes

- Bayesian posterior error
- provenance reconstruction error
- echo inflation
- downstream decision regret / hard-constraint violation
- false-claim uptake
- neutral-vs-defensive robustness gap
- later: attacker Flip Cost in the synthetic-web agent track

## Main claim to test

LLM agents overcount derivative evidence relative to its information value; strategic source multiplication can therefore create manufactured consensus that corrupts belief and decision-making.

## Why it matters

AI systems are becoming research and recommendation intermediaries. Search visibility and apparent source diversity can become de facto epistemic authority unless agents reason about where evidence actually originated.

## Minimum publishable experiment

Run the frozen Core and Marketing suites blindly across multiple model families with repeated epochs, then add the synthetic-web agent track only after the controlled signal is established. Compare vanilla prompting with the provenance-aware defense using the same hidden worlds.
