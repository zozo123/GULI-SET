# GullibleBench v1.0 results included with the release

## Deterministic calibration baselines

| Baseline | Core strict pass | Core posterior MAE | Marketing strict pass | Hard-constraint violation |
|---|---:|---:|---:|---:|
| Oracle | 100.0% | 0.0000 | 100.0% | 0.0% |
| Naive page counter | 62.5% | 0.0673 | 37.5% | 62.5% |

The naive baseline intentionally treats derivative pages as independent evidence and trusts the apparent marketing majority. Its failures demonstrate that the benchmark has useful score dynamic range.

### Naive Marketing strict pass by attack

| Attack | Strict pass |
|---|---:|
| plain false | 100% |
| selective omission | 100% |
| unsupported precision | 100% |
| authority laundering | 0% |
| benchmark laundering | 0% |
| manufactured consensus | 0% |
| circular citation | 0% |
| full stack | 0% |

This is a calibration baseline, not a claim about any LLM.

## Agent-track Flip Cost

Exact minimum attacker budget that flips each pre-registered reader policy, predicate `choice`, 64 cases, budget cap 16. Full tables for all three predicates are in [`FLIP_COST.md`](FLIP_COST.md) and the machine-readable artifact is `flip-cost.json`.

| Reader | Clean accuracy | Mean flip cost | Restricted mean | Zero-cost flips |
|---|---:|---:|---:|---:|
| `bounded-page-counter` | 38% | 0.38 | 0.38 | 62% |
| `+collapse_provenance` | 38% | 0.38 | 0.38 | 62% |
| `+guard_constraints` | 75% | 2.12 | 2.12 | 25% |
| `+verify_independence` | 75% | 2.12 | 2.12 | 25% |
| `+seek_primary_evidence` | 100% | 9.12 | 9.12 | 0% |

Top-rung flip cost by attack family, showing that campaigns which already crowd the ranking hand the attacker a discount:

| Attack | Flip cost |
|---|---:|
| manufactured consensus | 6 |
| full stack | 7 |
| circular citation | 8 |
| authority laundering | 9 |
| benchmark laundering | 9 |
| plain false | 11 |
| unsupported precision | 11 |
| selective omission | 12 |

**Interpretation:** this is a defense calibration curve, not a claim about any LLM. The reader policies are deterministic and consume provenance annotations withheld from models, so each rung upper-bounds what a perfect-provenance defense achieves. The sound comparison for a model result is against `bounded-page-counter`: flipping more cheaply than rung 0 means doing worse than counting pages.

Two results here are load-bearing for the benchmark's premise, and both satisfy go/no-go criterion 4 in [`../docs/PROTOCOL.md`](../docs/PROTOCOL.md).

62% of agent cases flip rung 0 at zero attacker cost, by two distinct mechanisms:

| Mechanism | Cases | Attacks | What happens |
|---|---:|---|---|
| Source topology | 24 | authority laundering, benchmark laundering, circular citation | the lab measurement **is** read, and loses 3:1 or 4:1 to a page count |
| Search ranking | 16 | manufactured consensus, full stack | boosted campaign pages fill all five read slots; the lab is never opened |

The second result is that the full Meta-harness stack — 100% strict pass on the non-agent Marketing track — still flips at zero cost on 25% of agent cases. In every case above, the decisive measurement is present and reachable in the synthetic web the whole time.

## GPT-5.6 Sol current-session sanity baseline

| Track | n | Strict pass | Choice accuracy | Provenance MAE | Other |
|---|---:|---:|---:|---:|---|
| Core representative slice | 6 | 100% | 100% | 0.0 | posterior MAE ~8.8e-12 |
| Marketing representative slice | 6 | 100% | 100% | 0.0 | claim audit 100%; violations 0% |

**Interpretation:** this result is deliberately not leaderboard eligible. GPT-5.6 Sol had already seen the benchmark hypothesis, examples, and intended provenance defense in the same conversation, and only a representative slice was evaluated. It is useful as an end-to-end parser/scorer sanity check and as evidence that the explicit/direct track is not sufficient by itself to challenge a benchmark-aware frontier model.

The next publishable result must be a fresh, blind run in isolated contexts on the neutral dataset, followed by the synthetic-web agent track. The agent track is now measurable end to end: `inspect_tasks.py@marketing_agent_attacked` sweeps an attacker budget and each sample carries the deterministic reference cost for the same case.

Exact response and score artifacts:

- `gpt-5.6-sol-current-session-responses.json`
- `gpt-5.6-sol-current-session-summary.json`
