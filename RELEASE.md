# GullibleBench v1.0.0

## Unreleased: release integrity

- Runtime version now derives from installed package metadata, eliminating the observed
  `1.0.0` versus `1.1.0` split.
- The SHA-256 manifest is executable and CI-enforced over every tracked file.
- CI pins third-party actions to immutable commits with read-only permissions.
- CI builds sdist and wheel, installs the wheel outside the checkout, and runs the demo.
- `CITATION.cff` now includes the author entity required for complete citation metadata.

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

## Agent-track Flip Cost — package 1.1.0 (2026-08-27)

The last metric listed as planned in `README.md` and `paper/PROPOSAL.md` is now implemented.

Two version numbers are deliberately distinct. The **package** is 1.1.0: a new backwards-compatible metric and CLI command. The **benchmark datasets remain GullibleBench v1.0** — every row in `data/` and every calibration number in `results/deterministic-baselines.json` is byte-identical, so v1.0 results stay directly comparable and remain citable as v1.0.

Flip Cost is the exact minimum attacker budget that flips a deterministic bounded-attention reader on the synthetic-web agent track. It measures a defense rather than a model, is computed by exhaustive search over a frozen price table, and requires no API key.

### Added

- `src/gulliblebench/flipcost.py`: typed attacker actions, the frozen price table, five pre-registered reader policies, and exact minimum-cost search
- `gulliblebench flip-cost`, writing `results/flip-cost.json` and `results/FLIP_COST.md`
- `docs/FLIP_COST.md`: threat model, price table, metric vector, and limitations
- `examples/flip_cost_demo.py` and `figures/flip_cost_ladder.png`
- 47 tests, including exact minimality verified against independent brute force, oracle-freedom of every reader, and immutability of product truth under attack
- `scripts/export_huggingface.py` and `docs/HUGGINGFACE.md` for Hub publication, with answer keys withheld by default
- CI now runs `flip-cost` and every example, lints `scripts` and `examples`, and asserts `git diff --exit-code -- data results`

### Changed

- `meta_harness`: the three `PolicyLayer` constants are public, and `solve_with_stack` accepts an optional base answer so one set of audited layer semantics serves both the Meta demo and the Flip Cost reader ladder. Demo output is byte-identical.

### Flip Cost snapshot

Predicate `choice`, 64 agent cases, budget cap 16:

| Reader | Clean accuracy | Grounded | Mean flip cost | Zero-cost flips |
|---|---:|---:|---:|---:|
| `bounded-page-counter` | 38% | 75% | 0.38 | 62% |
| `+collapse_provenance` | 38% | 75% | 0.38 | 62% |
| `+guard_constraints` | 75% | 75% | 2.12 | 25% |
| `+verify_independence` | 75% | 75% | 2.12 | 25% |
| `+seek_primary_evidence` | 100% | 100% | 9.12 | 0% |

### Known limits, stated up front

- The reader ladder consumes hidden provenance annotations that models never see, so each rung is an upper bound on a perfect-provenance defense rather than a model-comparable baseline.
- Rung 1 (`+collapse_provenance`) is inert under all three binary predicates; it reduces provenance error magnitude, which a binary flip predicate cannot see.
- The ladder is not monotone: rung 5 is strictly easier to attack than rung 4 on the audit predicate, because reading more exposes it to a forged measurement.
- `launder` and `bury_lab` are priced out under this table and never appear in a minimal plan.
- An unflippable result means "not flippable within the budget cap", never "provably safe".
- `clean_accuracy` is exactly `1 - already_flipped_rate` by construction, so it is not a second
  axis. `primary_evidence_read_rate` is the statistic that actually detects a useless defense: a
  reader with `read_limit=1` scores 100% clean and 62% unflippable on `audit` while grounding 0%.

The frozen v1.0 datasets, calibration baselines, and reported results are unchanged; the reproducibility gate above proves it byte-for-byte.
