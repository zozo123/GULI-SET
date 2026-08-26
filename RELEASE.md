# GullibleBench v1.0.0

Release date: 2026-08-23

## Included

- 48 exact-Bayesian Core cases
- 64 neutral synthetic Marketing cases
- 64 matched defensive-prompt Marketing cases
- 64 synthetic-web Agent prompts
- deterministic `search()` / `open()` environment
- eight synthetic campaign families
- exact programmatic scorers
- oracle and deliberately gullible calibration baselines
- GPT-5.6 Sol current-session sanity baseline (explicitly contaminated/non-leaderboard)
- optional Inspect AI Core, Marketing, and Marketing Agent tasks
- 25 unit/invariant tests
- baseline and normative figures
- research protocol, threat model, related work, reproducibility notes, and proposal

## Baseline snapshot

- Oracle: Core 100% strict; Marketing 100% strict
- Naive page counter: Core 62.5% strict; Marketing 37.5% strict; 62.5% hard-constraint violations
- GPT-5.6 Sol current-session slice: Core 100% strict (n=6); Marketing 100% strict (n=6); not leaderboard eligible

## Next scientific run

Blind, fresh-context evaluation across multiple model families on neutral/direct and agent tracks with >=3 stochastic epochs, followed by the matched provenance-aware defense condition.

## GitHub demo layer (2026-08-27)

The GULI-SET repository adds a tiny deterministic recipe, a zero-API Meta-harness demonstration, three regression tests, and GitHub-first documentation. This teaching layer does not alter the frozen v1.0 benchmark datasets or the reported calibration results.
