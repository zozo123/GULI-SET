# GullibleBench Flip Cost

Minimum attacker budget that flips a deterministic bounded-attention reader on the
synthetic-web agent track. Flip Cost measures a defense, not a model.

Budget cap: 16. Price table: echo=1, seo_boost=1, launder=3, bury_lab=5, forge_measurement=8.

`unflippable` means no plan within the cap flipped the reader, never that the reader is
provably unflippable. Mean flip cost is taken over flippable cases only; censored cases
are reported as `unflippable` rather than imputed at the cap.

## Predicate: choice

| Reader | Layers | Mean flip cost | Median | Min | Zero-cost flips | Unflippable |
|---|---|---:|---:|---:|---:|---:|
| `bounded-page-counter` | none | 0.375 | 0.0 | 0 | 62.5% | 0.0% |
| `+collapse_provenance` | collapse_provenance | 0.375 | 0.0 | 0 | 62.5% | 0.0% |
| `+guard_constraints` | collapse_provenance, guard_constraints | 2.125 | 2.0 | 0 | 25.0% | 0.0% |
| `+verify_independence` | collapse_provenance, guard_constraints, verify_independence | 2.125 | 2.0 | 0 | 25.0% | 0.0% |
| `+seek_primary_evidence` | collapse_provenance, guard_constraints, verify_independence | 9.125 | 9.0 | 6 | 0.0% | 0.0% |

## Predicate: audit

| Reader | Layers | Mean flip cost | Median | Min | Zero-cost flips | Unflippable |
|---|---|---:|---:|---:|---:|---:|
| `bounded-page-counter` | none | 0.375 | 0.0 | 0 | 62.5% | 0.0% |
| `+collapse_provenance` | collapse_provenance | 0.375 | 0.0 | 0 | 62.5% | 0.0% |
| `+guard_constraints` | collapse_provenance, guard_constraints | 0.375 | 0.0 | 0 | 62.5% | 0.0% |
| `+verify_independence` | collapse_provenance, guard_constraints, verify_independence | 8.000 | 8.0 | 8 | 0.0% | 12.5% |
| `+seek_primary_evidence` | collapse_provenance, guard_constraints, verify_independence | 8.000 | 8.0 | 8 | 0.0% | 0.0% |

## Predicate: provenance

| Reader | Layers | Mean flip cost | Median | Min | Zero-cost flips | Unflippable |
|---|---|---:|---:|---:|---:|---:|
| `bounded-page-counter` | none | 0.375 | 0.0 | 0 | 62.5% | 0.0% |
| `+collapse_provenance` | collapse_provenance | 0.375 | 0.0 | 0 | 62.5% | 0.0% |
| `+guard_constraints` | collapse_provenance, guard_constraints | 0.375 | 0.0 | 0 | 62.5% | 0.0% |
| `+verify_independence` | collapse_provenance, guard_constraints, verify_independence | 8.000 | 8.0 | 8 | 0.0% | 12.5% |
| `+seek_primary_evidence` | collapse_provenance, guard_constraints, verify_independence | 8.000 | 8.0 | 8 | 0.0% | 0.0% |

