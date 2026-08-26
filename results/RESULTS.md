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

## GPT-5.6 Sol current-session sanity baseline

| Track | n | Strict pass | Choice accuracy | Provenance MAE | Other |
|---|---:|---:|---:|---:|---|
| Core representative slice | 6 | 100% | 100% | 0.0 | posterior MAE ~8.8e-12 |
| Marketing representative slice | 6 | 100% | 100% | 0.0 | claim audit 100%; violations 0% |

**Interpretation:** this result is deliberately not leaderboard eligible. GPT-5.6 Sol had already seen the benchmark hypothesis, examples, and intended provenance defense in the same conversation, and only a representative slice was evaluated. It is useful as an end-to-end parser/scorer sanity check and as evidence that the explicit/direct track is not sufficient by itself to challenge a benchmark-aware frontier model.

The next publishable result must be a fresh, blind run in isolated contexts on the neutral dataset, followed by the synthetic-web agent track.

Exact response and score artifacts:

- `gpt-5.6-sol-current-session-responses.json`
- `gpt-5.6-sol-current-session-summary.json`
