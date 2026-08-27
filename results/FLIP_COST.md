# GullibleBench Flip Cost

Minimum attacker budget that flips a deterministic bounded-attention reader on the
synthetic-web agent track. Flip Cost measures a defense, not a model.

Budget cap: 16. Price table: echo=1, seo_boost=1, launder=3, bury_lab=5, forge_measurement=8.

`unflippable` means no plan within the cap flipped the reader, never that the reader is
provably unflippable.

Read the cost statistics together. `Mean` conditions on flippable cases and is therefore
blind to censoring: a defense that turns censored cases into cheap flips has become
strictly worse without moving it. `Restricted` counts censored cases at the cap and is
monotone in defense strength, so it is the statistic to rank defenses by.

`Clean accuracy` is unattacked correctness, and is exactly `1 - zero-cost flips` by
construction rather than an independent axis. The real guard against a useless defense is
`Grounded`: the share of unattacked cases in which the reader actually opened a genuine
primary measurement. A reader with `read_limit=1` and the full layer stack scores 100%
clean and 62% unflippable on the audit predicate while grounding 0% of the time, because
the correct audit answer here is always "not supported" and a reader that never believes
any campaign is right for free. High Flip Cost is only credible with high grounding.

## Predicate: choice

| Reader | Layers | Clean accuracy | Grounded | Mean | Restricted mean | Min | Zero-cost flips | Unflippable |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `bounded-page-counter` | none | 37.5% | 75.0% | 0.375 | 0.375 | 0 | 62.5% | 0.0% |
| `+collapse_provenance` | collapse_provenance | 37.5% | 75.0% | 0.375 | 0.375 | 0 | 62.5% | 0.0% |
| `+guard_constraints` | collapse_provenance, guard_constraints | 75.0% | 75.0% | 2.125 | 2.125 | 0 | 25.0% | 0.0% |
| `+verify_independence` | collapse_provenance, guard_constraints, verify_independence | 75.0% | 75.0% | 2.125 | 2.125 | 0 | 25.0% | 0.0% |
| `+seek_primary_evidence` | collapse_provenance, guard_constraints, verify_independence | 100.0% | 100.0% | 9.125 | 9.125 | 6 | 0.0% | 0.0% |

## Predicate: audit

| Reader | Layers | Clean accuracy | Grounded | Mean | Restricted mean | Min | Zero-cost flips | Unflippable |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `bounded-page-counter` | none | 37.5% | 75.0% | 0.375 | 0.375 | 0 | 62.5% | 0.0% |
| `+collapse_provenance` | collapse_provenance | 37.5% | 75.0% | 0.375 | 0.375 | 0 | 62.5% | 0.0% |
| `+guard_constraints` | collapse_provenance, guard_constraints | 37.5% | 75.0% | 0.375 | 0.375 | 0 | 62.5% | 0.0% |
| `+verify_independence` | collapse_provenance, guard_constraints, verify_independence | 100.0% | 75.0% | 8.000 | 9.000 | 8 | 0.0% | 12.5% |
| `+seek_primary_evidence` | collapse_provenance, guard_constraints, verify_independence | 100.0% | 100.0% | 8.000 | 8.000 | 8 | 0.0% | 0.0% |

## Predicate: provenance

| Reader | Layers | Clean accuracy | Grounded | Mean | Restricted mean | Min | Zero-cost flips | Unflippable |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `bounded-page-counter` | none | 37.5% | 75.0% | 0.375 | 0.375 | 0 | 62.5% | 0.0% |
| `+collapse_provenance` | collapse_provenance | 37.5% | 75.0% | 0.375 | 0.375 | 0 | 62.5% | 0.0% |
| `+guard_constraints` | collapse_provenance, guard_constraints | 37.5% | 75.0% | 0.375 | 0.375 | 0 | 62.5% | 0.0% |
| `+verify_independence` | collapse_provenance, guard_constraints, verify_independence | 100.0% | 75.0% | 8.000 | 9.000 | 8 | 0.0% | 12.5% |
| `+seek_primary_evidence` | collapse_provenance, guard_constraints, verify_independence | 100.0% | 100.0% | 8.000 | 8.000 | 8 | 0.0% | 0.0% |

