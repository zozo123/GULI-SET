"""Stage and publish GullibleBench as a Hugging Face Hub dataset repository.

The Hub copy is a *distribution channel*, not a second source of truth. Every row it
carries is regenerated deterministically by ``gulliblebench generate-all``; this script
only selects which generated files belong in public, validates them, writes a dataset
card whose ``configs`` block matches the staged files exactly, and (optionally) uploads.

Hidden-split policy
-------------------
The ``*-hidden.jsonl`` files are the symbolic answer keys and the full attack topology.
``docs/REPRODUCIBILITY.md`` says not to put hidden JSONL in front of models and to keep
evaluation worlds private for a leaderboard release; ``docs/BASELINE_POLICY.md`` treats
any run that has seen the design as leaderboard-ineligible. A crawled Hub copy of the
answer keys makes that contamination permanent and untraceable, so hidden splits are
**excluded by default**. Nothing is lost: the generator is the answer key, and the files
stay in the git repository. ``--include-hidden`` publishes them anyway, deliberately, and
the generated card then states that the repository carries its own answer keys.

This module imports only the standard library. ``huggingface_hub`` is not a dependency of
this project and is imported lazily inside :func:`upload_staging_dir`.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPO_ID = "zozo-ib/gulliblebench"
DEFAULT_STAGING_DIR = "build/huggingface"
DEFAULT_COMMIT_MESSAGE = "Publish GullibleBench v1.0 splits"
PROJECT_URL = "https://github.com/zozo123/GULI-SET"
BENCHMARK_VERSION = "1.0.0"
RELEASE_DATE = "2026-08-23"

#: Every staged split is evaluation-only, so there is one HF split name and it is not "train".
HF_SPLIT_NAME = "test"

VISIBLE_TARGET_KEYS = ("independent_evidence_units", "posterior_b", "truth")
MARKETING_TARGET_KEYS = (
    "campaign_claim_supported",
    "choice",
    "independent_supporting_origins",
)


@dataclass(frozen=True, slots=True)
class Split:
    """One JSONL file staged as one Hugging Face dataset configuration."""

    config: str
    source: str
    row_keys: tuple[str, ...]
    target_keys: tuple[str, ...]
    summary: str
    answer_key: bool = False

    def __post_init__(self) -> None:
        if not self.config:
            raise ValueError("config must be non-empty")
        if not self.source.endswith(".jsonl"):
            raise ValueError(f"{self.config}: source must be a .jsonl file")
        if not self.row_keys:
            raise ValueError(f"{self.config}: row_keys must be non-empty")
        if self.target_keys and "target" not in self.row_keys:
            raise ValueError(f"{self.config}: target_keys given without a target row key")


#: Model-visible splits. These are the prompts a model or agent is allowed to see.
VISIBLE_SPLITS: tuple[Split, ...] = (
    Split(
        config="core",
        source="core.jsonl",
        row_keys=("id", "metadata", "prompt", "target"),
        target_keys=VISIBLE_TARGET_KEYS,
        summary="Exact Bayesian correlation-neglect cases; echoed vs independent origins.",
    ),
    Split(
        config="marketing-neutral",
        source="marketing-neutral.jsonl",
        row_keys=("id", "metadata", "prompt", "target"),
        target_keys=MARKETING_TARGET_KEYS,
        summary="Direct marketing evaluation under neutral instructions.",
    ),
    Split(
        config="marketing-defensive",
        source="marketing-defensive.jsonl",
        row_keys=("id", "metadata", "prompt", "target"),
        target_keys=MARKETING_TARGET_KEYS,
        summary="The same worlds under matched provenance-aware instructions.",
    ),
    Split(
        config="agent",
        source="agent.jsonl",
        row_keys=("id", "metadata", "prompt", "target"),
        target_keys=MARKETING_TARGET_KEYS,
        summary="Page-hidden synthetic-web prompts for the search/open agent track.",
    ),
)

#: Answer keys. Excluded unless ``--include-hidden`` is passed. See the module docstring.
HIDDEN_SPLITS: tuple[Split, ...] = (
    Split(
        config="core-hidden",
        source="core-hidden.jsonl",
        row_keys=(
            "evidence_origins",
            "id",
            "metadata",
            "pages",
            "prior_b",
            "provenance_edges",
            "truth",
        ),
        target_keys=(),
        summary="Symbolic Core worlds: origins, pages, provenance edges, truth.",
        answer_key=True,
    ),
    Split(
        config="marketing-hidden",
        source="marketing-hidden.jsonl",
        row_keys=(
            "attack",
            "campaign_claim",
            "correct_side",
            "id",
            "pages",
            "products",
            "prompt",
            "requirement_budget_usd",
            "requirement_latency_ms",
            "target_side",
        ),
        target_keys=(),
        summary="Symbolic Marketing worlds: product truth, page provenance, attack label.",
        answer_key=True,
    ),
)

MANAGED_NAMES: tuple[str, ...] = tuple(
    [split.source for split in VISIBLE_SPLITS + HIDDEN_SPLITS] + ["README.md", "LICENSE"]
)


def selected_splits(*, include_hidden: bool) -> tuple[Split, ...]:
    return VISIBLE_SPLITS + HIDDEN_SPLITS if include_hidden else VISIBLE_SPLITS


def validate_jsonl(split: Split, path: Path) -> int:
    """Return the row count, raising ``ValueError`` on the first malformed row."""

    if not path.is_file():
        raise ValueError(f"{split.config}: missing source file {path}")
    rows = 0
    with path.open(encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, start=1):
            if not line.strip():
                raise ValueError(f"{path}:{lineno}: blank line in JSONL")
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{lineno}: not valid JSON: {exc}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{lineno}: row must be a JSON object")
            missing = [key for key in split.row_keys if key not in row]
            if missing:
                raise ValueError(f"{path}:{lineno}: missing keys {missing}")
            if split.target_keys:
                target = row["target"]
                if not isinstance(target, dict):
                    raise ValueError(f"{path}:{lineno}: target must be a JSON object")
                missing_targets = [key for key in split.target_keys if key not in target]
                if missing_targets:
                    raise ValueError(f"{path}:{lineno}: target missing keys {missing_targets}")
            rows += 1
    if rows == 0:
        raise ValueError(f"{path}: no rows")
    return rows


def _size_category(total_rows: int) -> str:
    if total_rows < 1_000:
        return "n<1K"
    if total_rows < 10_000:
        return "1K<n<10K"
    return "10K<n<100K"


def _frontmatter(counts: tuple[tuple[Split, int], ...]) -> list[str]:
    total = sum(rows for _, rows in counts)
    lines = [
        "---",
        "license: mit",
        "language:",
        "- en",
        "pretty_name: GullibleBench (GULI-SET)",
        "size_categories:",
        f"- {_size_category(total)}",
        "task_categories:",
        "- question-answering",
        "- text-classification",
        "tags:",
        "- benchmark",
        "- evaluation",
        "- provenance",
        "- misinformation-robustness",
        "- synthetic",
        "- causal-inference",
        "- agents",
        "configs:",
    ]
    for split, _ in counts:
        lines += [
            f"- config_name: {split.config}",
            "  data_files:",
            f"  - split: {HF_SPLIT_NAME}",
            f"    path: {split.source}",
        ]
    lines.append("---")
    return lines


def dataset_card(counts: tuple[tuple[Split, int], ...], *, include_hidden: bool) -> str:
    """Render the Hub dataset card for exactly the splits that were staged."""

    lines = _frontmatter(counts)
    lines += [
        "",
        "# GullibleBench v1.0 (GULI-SET)",
        "",
        "> Can a model tell the difference between five independent measurements and one",
        "> claim copied five times?",
        "",
        "GullibleBench is a deterministic, fully synthetic causal benchmark for manufactured",
        "consensus. Matched counterfactuals hold page count, claim direction, and source",
        "reliability fixed and vary only evidentiary independence, so a score difference is",
        "attributable to correlation neglect rather than to prompt wording.",
        "",
        f"Code, generator, scorers, and protocol: {PROJECT_URL}",
        "",
        "## Read this before using the data",
        "",
        "- **Everything is synthetic and fictional.** All products, vendors, laboratories,",
        "  measurements, URLs, and campaigns are generated. There are no real brands, no real",
        "  search engine, no live web access, and no real misinformation in this dataset. The",
        "  synthetic web is a closed `search()` / `open()` world with deterministic rankings.",
        "- **Symbolic truth is authoritative; prose is only a rendering.** The `prompt` field is",
        "  a deterministic rendering of a symbolic world. If a rendering and the symbolic world",
        "  ever disagree, the symbolic world is correct and the renderer is the bug.",
        "- **Primary scores are programmatic.** Answers are strict JSON and are scored by exact",
        "  arithmetic and set comparison. No LLM judge is used or required.",
        "- **Contamination warning.** A model that has seen the research hypothesis, the intended",
        "  defense, or the target values is a sanity check, not a leaderboard entry. Because",
        "  every row published here carries its `target`, this Hub copy is itself a contamination",
        "  surface: use fresh isolated contexts, and regenerate rotated worlds from the",
        "  generator in the repository for any result you intend to publish.",
        "",
        "## Splits",
        "",
        "| Config | Rows | Contents |",
        "|---|---:|---|",
    ]
    for split, rows in counts:
        lines.append(f"| `{split.config}` | {rows} | {split.summary} |")
    lines += [
        "",
        f"Each config has a single `{HF_SPLIT_NAME}` split. There is no training split: this is",
        "an evaluation set, and fine-tuning on it destroys its measurement value.",
        "",
        "## Row schema",
        "",
        "Model-visible rows carry `id`, `prompt`, `metadata`, and `target`.",
        "",
        "- `core`: `target.posterior_b` is the exact Bayesian posterior computed from unique",
        "  evidence origins, `target.independent_evidence_units` is the origin count, and",
        "  `target.truth` is the superior product.",
        "- `marketing-neutral`, `marketing-defensive`, `agent`: `target.choice` is the product",
        "  that actually satisfies the user's hard requirements,",
        "  `target.campaign_claim_supported` is `false` for every v1 case, and",
        "  `target.independent_supporting_origins` is `0` for every v1 case.",
        "",
        "The two marketing conditions render the same worlds under neutral and",
        "provenance-aware instructions, which is what makes the defense gap measurable.",
        "",
        "## Attack families",
        "",
        "Eight base worlds cross eight campaign families, mirrored across products A and B:",
        "plain falsehood, selective omission, unsupported precision, authority laundering,",
        "benchmark laundering, manufactured consensus, circular citation, and a full-stack",
        "campaign. The promoted product always violates the stated hard latency requirement,",
        "the alternative satisfies every hard requirement, and exactly one independent",
        "measurement exposes the true latency. Marketing pages never alter product truth.",
        "",
        "## Agent track and Flip Cost",
        "",
        "The `agent` config withholds the pages and expects the model to use the synthetic",
        "`search()` / `open()` tools. The repository also reports **Flip Cost**: the exact",
        "minimum attacker budget, priced from a frozen pre-registered action table, that flips",
        "a deterministic bounded-attention reader's decision. Flip Cost is a property of a",
        "defense, not of a model, and it is measured by exhaustive search rather than",
        "estimated.",
        "",
        "## Hidden splits",
        "",
    ]
    if include_hidden:
        lines += [
            "This repository **includes** the `*-hidden` answer-key configs, published",
            "deliberately with `--include-hidden`. They contain full symbolic worlds: product",
            "truth, page provenance, and attack labels. Any model whose training data may",
            "include this repository must be treated as contaminated for GullibleBench, and",
            "leaderboard-grade results require freshly generated, unpublished worlds.",
        ]
    else:
        lines += [
            "The `*-hidden.jsonl` answer keys are **not published here**. They are the symbolic",
            "audit worlds, and putting them on a crawlable host would permanently contaminate",
            "the benchmark for every later model. They remain in the git repository, and the",
            "generator reproduces them byte-for-byte:",
            "",
            "```bash",
            "pip install -e .",
            "gulliblebench generate-all",
            "```",
            "",
            "Release data hashes are recorded in `MANIFEST.sha256` in the repository.",
        ]
    lines += [
        "",
        "## Scoring",
        "",
        "```bash",
        "pip install -e '.[dev]'",
        "gulliblebench score-core   <responses.jsonl>",
        "gulliblebench score-marketing <responses.jsonl>",
        "```",
        "",
        "Report the metric vector and the strict pass rate; do not collapse them to one",
        "composite. Formatting failures are reported separately from epistemic failures. See",
        "`docs/PROTOCOL.md`, `docs/BASELINE_POLICY.md`, and `docs/REPRODUCIBILITY.md` in the",
        "repository.",
        "",
        "## Intended use",
        "",
        "GullibleBench measures defenses against deceptive information ecosystems. It is not a",
        "toolkit for deploying deception: real brand targeting, publishing pages to the live",
        "web, poisoning production indexes, impersonating real institutions, and",
        "prompt-injection payloads are all out of scope by construction",
        "(`docs/THREAT_MODEL.md`).",
        "",
        "## Citation",
        "",
        f"Citation metadata is in `CITATION.cff` at {PROJECT_URL}.",
        "",
        "```bibtex",
        "@software{gulliblebench,",
        "  title  = {GullibleBench},",
        "  author = {{GullibleBench contributors}},",
        f"  version = {{{BENCHMARK_VERSION}}},",
        f"  year   = {{{RELEASE_DATE[:4]}}},",
        f"  date   = {{{RELEASE_DATE}}},",
        "  license = {MIT},",
        f"  url    = {{{PROJECT_URL}}}",
        "}",
        "```",
        "",
        "MIT licensed; see `LICENSE` in this repository.",
        "",
    ]
    return "\n".join(lines)


def _clean_managed(staging_dir: Path, keep: frozenset[str]) -> list[str]:
    """Remove previously staged files we manage that are not part of this run."""

    removed = []
    for name in MANAGED_NAMES:
        if name in keep:
            continue
        path = staging_dir / name
        if path.is_file():
            path.unlink()
            removed.append(name)
    return removed


def stage(
    staging_dir: Path, *, data_dir: Path, license_path: Path, include_hidden: bool
) -> tuple[tuple[Split, int], ...]:
    """Validate the source JSONL, then write the staging directory. Returns row counts."""

    splits = selected_splits(include_hidden=include_hidden)
    counts = tuple((split, validate_jsonl(split, data_dir / split.source)) for split in splits)
    if not license_path.is_file():
        raise ValueError(f"missing license file {license_path}")

    staging_dir.mkdir(parents=True, exist_ok=True)
    keep = frozenset([split.source for split in splits] + ["README.md", "LICENSE"])
    for name in _clean_managed(staging_dir, keep):
        print(f"removed stale {name}")
    for split, _ in counts:
        shutil.copyfile(data_dir / split.source, staging_dir / split.source)
    shutil.copyfile(license_path, staging_dir / "LICENSE")
    card = dataset_card(counts, include_hidden=include_hidden)
    (staging_dir / "README.md").write_text(card, encoding="utf-8")
    return counts


def unmanaged_entries(staging_dir: Path) -> tuple[str, ...]:
    managed = set(MANAGED_NAMES)
    return tuple(sorted(entry.name for entry in staging_dir.iterdir() if entry.name not in managed))


def upload_staging_dir(
    staging_dir: Path, *, repo_id: str, private: bool, commit_message: str
) -> str:
    """Create the dataset repo if needed and upload the staging directory."""

    try:
        from huggingface_hub import HfApi
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "huggingface_hub is required to upload and is deliberately not a dependency of "
            "this project.\n"
            "Install it in an isolated tool environment:\n"
            "    uv tool install huggingface_hub\n"
            "or into the active environment:\n"
            "    pip install huggingface_hub\n"
            "Then authenticate once:  hf auth login"
        ) from exc

    api = HfApi()
    api.create_repo(repo_id=repo_id, repo_type="dataset", private=private, exist_ok=True)
    return str(
        api.upload_folder(
            folder_path=str(staging_dir),
            repo_id=repo_id,
            repo_type="dataset",
            commit_message=commit_message,
        )
    )


def _print_plan(
    counts: tuple[tuple[Split, int], ...],
    staging_dir: Path,
    *,
    repo_id: str,
    private: bool,
    commit_message: str,
    include_hidden: bool,
    dry_run: bool,
) -> None:
    print("staged files")
    for split, rows in counts:
        flag = "  [ANSWER KEY]" if split.answer_key else ""
        print(f"  {split.source:<28} {rows:>4} rows  config={split.config}{flag}")
    print(f"  {'README.md':<28}    generated dataset card")
    print(f"  {'LICENSE':<28}    copied from LICENSE")
    extra = unmanaged_entries(staging_dir)
    if extra:
        print(
            f"warning: staging dir also contains unmanaged files, which would be uploaded: "
            f"{', '.join(extra)}"
        )
    print()
    print(f"repo id         {repo_id}")
    print("repo type       dataset")
    print(f"visibility      {'private' if private else 'public'}")
    print(f"hidden splits   {'INCLUDED' if include_hidden else 'excluded (answer keys withheld)'}")
    print(f"staging dir     {staging_dir}")
    print(f"commit message  {commit_message}")
    print(f"total rows      {sum(rows for _, rows in counts)}")
    print()
    if dry_run:
        print("dry run: nothing was uploaded. Equivalent upload:")
        print(f"  hf upload {repo_id} {staging_dir} --repo-type dataset")
        print("Re-run with --no-dry-run to publish.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="export_huggingface.py",
        description="Stage and optionally publish GullibleBench to the Hugging Face Hub.",
    )
    parser.add_argument("--repo-id", default=DEFAULT_REPO_ID, help="target Hub dataset repo id")
    parser.add_argument(
        "--staging-dir",
        default=DEFAULT_STAGING_DIR,
        help=f"directory to build (default: {DEFAULT_STAGING_DIR})",
    )
    parser.add_argument(
        "--data-dir", default=str(REPO_ROOT / "data"), help="directory holding the JSONL splits"
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="also publish the *-hidden answer keys (contaminates the benchmark; off by default)",
    )
    parser.add_argument("--private", action="store_true", help="create the dataset repo as private")
    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="stage and validate without uploading (default: --dry-run)",
    )
    parser.add_argument(
        "--commit-message", default=DEFAULT_COMMIT_MESSAGE, help="Hub commit message"
    )
    args = parser.parse_args(argv)

    staging_dir = Path(args.staging_dir).expanduser()
    if not staging_dir.is_absolute():
        staging_dir = REPO_ROOT / staging_dir
    data_dir = Path(args.data_dir).expanduser()
    if not data_dir.is_absolute():
        data_dir = REPO_ROOT / data_dir

    try:
        counts = stage(
            staging_dir,
            data_dir=data_dir,
            license_path=REPO_ROOT / "LICENSE",
            include_hidden=args.include_hidden,
        )
    except ValueError as exc:
        raise SystemExit(f"validation failed: {exc}") from exc

    if args.include_hidden:
        print("warning: --include-hidden publishes the answer keys; see docs/HUGGINGFACE.md")
    _print_plan(
        counts,
        staging_dir,
        repo_id=args.repo_id,
        private=args.private,
        commit_message=args.commit_message,
        include_hidden=args.include_hidden,
        dry_run=args.dry_run,
    )
    if args.dry_run:
        return 0

    url = upload_staging_dir(
        staging_dir,
        repo_id=args.repo_id,
        private=args.private,
        commit_message=args.commit_message,
    )
    print(f"uploaded: {url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
