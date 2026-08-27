# Publishing to the Hugging Face Hub

`scripts/export_huggingface.py` stages a dataset repository from `data/`, validates it, writes
the dataset card, and uploads on request. It is standard-library only; `huggingface_hub` is
imported lazily inside the upload path and is deliberately not a project dependency.

Default target: `zozo-ib/gulliblebench` (dataset repo).

## What gets published

| Staged file | Config | Rows |
|---|---|---:|
| `core.jsonl` | `core` | 48 |
| `marketing-neutral.jsonl` | `marketing-neutral` | 64 |
| `marketing-defensive.jsonl` | `marketing-defensive` | 64 |
| `agent.jsonl` | `agent` | 64 |
| `README.md` | dataset card, generated | — |
| `LICENSE` | copy of the repository license | — |

Each config exposes a single `test` split. There is no `train` split, because fine-tuning on
an evaluation set destroys its measurement value. The card's `configs` block is generated from
the same list that stages the files, so the Hub dataset viewer cannot drift from the contents.

## Hidden-split policy

`core-hidden.jsonl` and `marketing-hidden.jsonl` are **excluded by default**.

They are the symbolic answer keys: product truth, page provenance, attack labels, evidence
origins. `docs/REPRODUCIBILITY.md` says not to place hidden JSONL in front of models and to
keep evaluation worlds private for a leaderboard release; `docs/BASELINE_POLICY.md` treats any
run that has seen the design as leaderboard-ineligible. A crawlable copy of the answer keys
makes that contamination permanent and untraceable, and it is not recoverable by rotating
seeds later.

Nothing is lost by withholding them. The generator is the answer key, and it is deterministic:

```bash
gulliblebench generate-all   # reproduces every file in data/, hashes in MANIFEST.sha256
```

Two things worth stating plainly rather than implying:

- The published splits still carry their `target` fields, so the Hub copy is a contamination
  surface too — just a much smaller one than the full symbolic worlds. The card says so.
- `--include-hidden` will publish the answer keys anyway. It prints a warning, marks the
  affected files `[ANSWER KEY]` in the plan, and switches the card's hidden-splits section to
  state that this repository carries its own answer keys. Use it only for a deliberately
  contaminated teaching copy, never for the leaderboard repository.

## Authenticate

The `hf` CLI stores a token that `huggingface_hub` reads automatically.

```bash
uv tool install huggingface_hub   # or: pip install huggingface_hub
hf auth login                     # needs a token with write access to the target namespace
hf auth whoami
```

## Dry run first

The dry run is the default; the script never uploads unless told to.

```bash
.venv/bin/python scripts/export_huggingface.py --dry-run
```

It builds `build/huggingface/` (gitignored), parses every JSONL line, checks the expected row
and `target` keys, prints a row count per split, and prints the upload it would perform. Any
malformed line fails with the file, line number, and reason, and nothing is uploaded.

Read the printed plan before continuing: repo id, visibility, hidden-split state, total rows.

## Publish

```bash
.venv/bin/python scripts/export_huggingface.py --no-dry-run \
  --commit-message "Publish GullibleBench v1.0 splits"
```

Useful flags: `--repo-id`, `--staging-dir`, `--private`, `--data-dir`, `--include-hidden`.

## Re-publish an update

Regenerate, verify, stage, then upload to the same repo id. Hub commits are additive, so an
update is just another commit with a message that says what changed.

```bash
gulliblebench generate-all
pytest
.venv/bin/python scripts/export_huggingface.py --dry-run
.venv/bin/python scripts/export_huggingface.py --no-dry-run \
  --commit-message "Regenerate v1.0 splits from <commit>"
```

Staging is idempotent: files this script manages are removed from the staging directory when
they are not part of the current run, so a `--include-hidden` build followed by a default build
does not leave answer keys behind. Files in the staging directory that the script does not
manage are reported as a warning, because `upload_folder` would publish them.

Data changes that alter any target are a new benchmark version, not an update. Bump the version
in `pyproject.toml` and `CITATION.cff`, refresh `MANIFEST.sha256`, and say so in the commit
message so that published results remain attributable to a specific dataset revision.
