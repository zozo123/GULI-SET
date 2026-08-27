# Reproducibility

## Local deterministic checks

```bash
uv venv --python 3.11
uv pip install -e '.[dev]'
.venv/bin/ruff check src tests scripts examples
.venv/bin/pytest
.venv/bin/gulliblebench demo
.venv/bin/gulliblebench generate-all
.venv/bin/gulliblebench baselines
.venv/bin/gulliblebench flip-cost
```

`python -m venv` and `pip install -e '.[dev]'` work identically; `uv` is simply faster.

Core and Marketing world generation is deterministic. Release data hashes are recorded in `MANIFEST.sha256`.

CI runs the sequence above and then asserts:

```bash
git diff --exit-code -- data results
```

Every file under `data/` and `results/` is therefore byte-reproducible from source on Python 3.11, 3.12, and 3.13. Flip Cost participates in this gate: it contains no randomness, no wall-clock, and no network access, and its plan enumeration is exhaustive rather than sampled.

`figures/` is deliberately **excluded** from that gate. Matplotlib PNG output is not byte-stable across matplotlib versions, so regenerating figures produces diffs that carry no information. The figures are checked in as published artifacts; `scripts/make_figures.py` reproduces them semantically, not byte-for-byte. Do not commit figure churn from a version bump.

## Model runs

For publishable model results:

- use a fresh context per sample;
- record exact provider/model identifier and evaluation date;
- record decoding parameters and number of epochs;
- run the neutral condition before exposing defensive prompts;
- do not provide hidden JSONL files to models;
- keep evaluation seeds/worlds private for a leaderboard release;
- report formatting failures separately from epistemic failures.

The response-file scorers enforce that policy mechanically. By default the submitted id set must
equal the benchmark id set. Parse failures count as strict failures and are listed by id. An
explicit `--allow-partial` exploration keeps missing cases in the top-level denominator and
reports both submission and parsed coverage. Core additionally reports coverage of all 18
matched echo/independent causal pairs.

Inspect AI adapters are provided for Core, direct Marketing, synthetic-web Marketing Agent, and attacked Marketing Agent tasks. CI installs the `[inspect]` extra and asserts that all four tasks actually construct with the expected sample counts and metadata, so the adapters are instantiation-verified rather than only syntax-checked. A live provider run still requires model credentials.

To measure empirical Flip Cost against a model, sweep the attacker budget:

```bash
inspect eval src/gulliblebench/inspect_tasks.py@marketing_agent_attacked \
    --model <provider/model> -T echo=6
```

Each sample carries `attacker_cost` and the pristine-case `reference_flip_cost_choice` for the top deterministic reader rung, so a model result can be placed on the pre-registered ladder in [`docs/FLIP_COST.md`](FLIP_COST.md) instead of being scored in isolation. A model that flips more cheaply than `bounded-page-counter` is doing worse than counting pages.

## Current-session GPT-5.6 Sol baseline

This is intentionally marked contaminated and non-blind. Re-run it through a clean model endpoint before citing it as a model result.
