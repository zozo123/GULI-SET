# GULI-SET

**Gullibility Under Laundered Information — a Stress & Evaluation Toolkit**

[![CI](https://github.com/zozo123/GULI-SET/actions/workflows/ci.yml/badge.svg)](https://github.com/zozo123/GULI-SET/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-2ea44f.svg)](LICENSE)

> Can an AI tell the difference between five independent measurements and one claim copied five times?

GULI-SET packages **GullibleBench v1.0**, a causal benchmark for manufactured consensus, with a tiny process-improvement lab inspired by [Meta\(^n\)](https://arxiv.org/abs/2608.24735). It is synthetic, deterministic, inspectable, and useful without an API key.

![Deterministic GullibleBench baseline scorecard](figures/baseline_scorecard.png)

## Run the 30-second demo

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
gulliblebench demo
```

```text
GULI-SET // META HARNESS
4 tasks · fixed Omega · deterministic · zero API keys

depth  stack                                      strict  audit   safe  prov MAE  Omega input
-----  -----------------------------------------  ------  ------  -----  --------  -----------
    0  base:page_counter                            25%    25%   25%     3.250            4
    1  + collapse_provenance                        25%    25%   25%     0.750            9
    2  + guard_constraints                          25%    25%  100%     0.750           14
    3  + verify_independence                       100%   100%  100%     0.000           19

emergent roles: compression -> routing -> verification
converged: no scored failures remain
```

The data is a [tiny recipe](data/demo.json). It expands into four deterministic GullibleBench attacks, runs a deliberately gullible page counter, scores its failures, and asks one **frozen** improver (`Omega`) for the next typed policy layer. Omega never rewrites itself. Its input grows with the trace history and installed stack.

```mermaid
flowchart LR
    D[4-case recipe] --> B[Naive page counter]
    B --> S[Exact scorer]
    S --> T[Growing trace history]
    K[Installed layer stack] --> O[Fixed Omega]
    T --> O
    O -->|next typed layer| K
    K --> B
    O -->|no useful layer| C[Converged]
```

This is an **educational control-pattern demo**, not a reproduction of Meta\(^n\). It uses deterministic, pre-registered layers instead of an LLM that writes executable helpers, and it has no evolutionary archive. See [the harness note](docs/META_HARNESS.md) and the [official Meta\(^n\) code](https://github.com/minnesotanlp/meta-n).

## The benchmark

### Core: exact correlation neglect

Matched counterfactuals hold page count, claim direction, and reliability fixed while changing only evidentiary independence:

- four pages copied from **one** 75%-reliable origin: `P(B)=0.75`
- four pages from **four independent** 75%-reliable origins: `P(B)=81/82 ≈ 0.987805`

A model that becomes more confident merely because one report was echoed is counting presentation volume as information.

### Marketing: strategic synthetic campaigns

A fictional product violates a hard latency requirement. One decisive lab measurement is surrounded by increasingly polished marketing:

1. plain falsehood
2. selective omission
3. unsupported precision
4. authority laundering
5. benchmark laundering
6. manufactured consensus
7. circular citation
8. a full-stack campaign

Every world is mirrored across products A/B. Neutral and provenance-aware prompts let you measure the defense gap instead of baking the answer into every condition.

### Synthetic Web: a closed `search()` / `open()` world

The same campaigns become miniature local websites with deterministic, attackable rankings. Nothing touches real brands, live search, or real misinformation.

## Data at a glance

| File | Rows | Purpose |
|---|---:|---|
| `data/demo.json` | 4-case recipe | smallest end-to-end Meta-harness run |
| `data/core.jsonl` | 48 | model-visible Bayesian correlation cases |
| `data/core-hidden.jsonl` | 48 | symbolic audit worlds; never model-visible |
| `data/marketing-neutral.jsonl` | 64 | neutral direct-evaluation prompts |
| `data/marketing-defensive.jsonl` | 64 | matched provenance-aware prompts |
| `data/marketing-hidden.jsonl` | 64 | campaign truth and provenance |
| `data/agent.jsonl` | 64 | page-hidden synthetic-web agent prompts |

Symbolic truth is authoritative; prose is only a rendering. Primary scores are programmatic—no LLM judge is required.

## Reproduce everything

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'

ruff check src tests
pytest
gulliblebench demo
gulliblebench generate-all
gulliblebench baselines
python examples/first_pair.py
python examples/synthetic_web_demo.py
```

For a machine-readable trace artifact:

```bash
gulliblebench demo --json > meta-demo-run.json
```

To change the tiny experiment, copy `data/demo.json`, select any of the eight attack names, and pass it with `--data`.

## Run real models with Inspect AI

[Inspect AI](https://inspect.aisi.org.uk/) is optional:

```bash
pip install -e '.[inspect]'
inspect eval src/gulliblebench/inspect_tasks.py@core --model <provider/model>
inspect eval src/gulliblebench/inspect_tasks.py@marketing --model <provider/model>
inspect eval src/gulliblebench/inspect_tasks.py@marketing_agent --model <provider/model>
```

Use fresh isolated sessions, hidden or rotating seeds, and repeated runs for publishable results. A model that has seen the hypothesis, defense, or targets is a sanity check—not a leaderboard entry.

## Included calibration results

| Baseline | Core strict pass | Core posterior MAE | Marketing strict pass | Hard-constraint violations |
|---|---:|---:|---:|---:|
| Oracle | 100.0% | 0.0000 | 100.0% | 0.0% |
| Naive page counter | 62.5% | 0.0673 | 37.5% | 62.5% |

The naïve baseline intentionally counts derivative pages as independent. Its failures establish score direction and dynamic range; they are not a claim about an LLM.

The included GPT-5.6 Sol slice scored 100%, but is explicitly marked **non-blind, contaminated, and leaderboard-ineligible** because the same session had already seen the benchmark design. See [`results/RESULTS.md`](results/RESULTS.md) and [`docs/BASELINE_POLICY.md`](docs/BASELINE_POLICY.md).

## Metrics

**Core:** posterior MAE, provenance-count MAE, choice accuracy, echo-specific posterior MAE, and strict pass.

**Marketing:** choice accuracy, false-claim audit accuracy, provenance-count MAE, hard-constraint violation rate, and strict pass.

The planned agent metric is **Flip Cost**: the smallest attacker budget that changes a belief or decision.

## Project map

```text
src/gulliblebench/       generators, worlds, scorers, CLI, Meta harness
data/                    visible, hidden, agent, and tiny demo data
tests/                   deterministic correctness and regression tests
docs/                    protocol, threats, baselines, reproducibility
results/                 calibration and clearly labeled sanity artifacts
figures/                 checked-in reproducible plots
examples/                minimal Python entry points
paper/PROPOSAL.md        research question and minimum experiment
```

## Scientific claim to test

> LLM agents systematically overweight derivative evidence relative to its information value, allowing strategically manufactured source diversity to corrupt beliefs and downstream decisions even when stronger contradictory evidence is available.

GULI-SET measures defenses against deceptive information ecosystems; it is not a toolkit for deploying deception. All products, sources, measurements, URLs, and campaigns are fictional.

## Citation and license

Benchmark citation metadata is in [`CITATION.cff`](CITATION.cff). The Meta-harness design is inspired by Kim et al., [*Meta\(^n\): Recursive Self-Improvement through Emergent Depth*](https://arxiv.org/abs/2608.24735); this repository is independent and is not their official implementation.

MIT licensed. See [`LICENSE`](LICENSE).
