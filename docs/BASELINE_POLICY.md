# Baseline policy

## Deterministic baselines

`oracle` is the ceiling and validates the scorer.

`naive-page-counter` deliberately treats each page as independent evidence and trusts marketing majority. It validates that GullibleBench penalizes correlation neglect and produces useful dynamic range.

## GPT-5.6 Sol current-session baseline

The repository contains a small sanity run produced by GPT-5.6 Sol in the same conversation that designed the benchmark.

It is **not a publishable or leaderboard result** because:

1. the model saw the research hypothesis and examples;
2. the model knew the intended defense;
3. only a representative slice was run;
4. there was no clean model API available in the execution environment for a fresh isolated batch run.

It is included because it is useful engineering evidence: parsing/scoring works end-to-end, and a benchmark-aware frontier model can solve the explicit/direct slice. A real baseline must be rerun blind through Inspect AI (or another reproducible model runner) in fresh contexts.
