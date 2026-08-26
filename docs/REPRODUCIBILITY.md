# Reproducibility

## Local deterministic checks

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
ruff check src tests
pytest
gulliblebench demo
gulliblebench generate-all
gulliblebench baselines
```

Core and Marketing world generation is deterministic. Release data hashes are recorded in `MANIFEST.sha256`.

## Model runs

For publishable model results:

- use a fresh context per sample;
- record exact provider/model identifier and evaluation date;
- record decoding parameters and number of epochs;
- run the neutral condition before exposing defensive prompts;
- do not provide hidden JSONL files to models;
- keep evaluation seeds/worlds private for a leaderboard release;
- report formatting failures separately from epistemic failures.

Inspect AI adapters are provided for Core, direct Marketing, and synthetic-web Marketing Agent tasks. The optional Inspect integration is syntax-checked in this release; a live provider run requires the relevant model credentials and `inspect-ai` dependency.

## Current-session GPT-5.6 Sol baseline

This is intentionally marked contaminated and non-blind. Re-run it through a clean model endpoint before citing it as a model result.
