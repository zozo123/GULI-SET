from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .dataset import CoreCase
from .evaluate import (
    CoreCausalSummary,
    CoreSummary,
    MarketingSummary,
    summarize_core,
    summarize_core_causal,
    summarize_marketing,
)
from .marketing import MarketingCase
from .marketing_scoring import MarketingAnswer, parse_marketing_answer, score_marketing
from .parsing import parse_answer
from .scoring import ParsedAnswer, score_core


@dataclass(frozen=True, slots=True)
class EvaluationCoverage:
    """Coverage and formatting diagnostics for one response file."""

    expected_n: int
    submitted_n: int
    parsed_n: int
    parse_failure_n: int
    missing_n: int
    submission_coverage: float
    parsed_coverage: float
    missing_ids: tuple[str, ...]
    parse_failures: dict[str, str]


@dataclass(frozen=True, slots=True)
class CoreResponseReport:
    coverage: EvaluationCoverage
    strict_pass_rate: float
    parsed_summary: CoreSummary | None
    causal_summary: CoreCausalSummary


@dataclass(frozen=True, slots=True)
class MarketingResponseReport:
    coverage: EvaluationCoverage
    strict_pass_rate: float
    parsed_summary: MarketingSummary | None


def _answer_text(value: object) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value)


def load_response_rows(path: str | Path) -> dict[str, object]:
    rows: dict[str, object] = {}
    with Path(path).open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"line {line_no}: invalid response JSONL: {exc.msg}") from exc
            if not isinstance(row, dict) or "id" not in row or "answer" not in row:
                raise ValueError(f"line {line_no}: expected object with id and answer")
            ident = str(row["id"])
            if ident in rows:
                raise ValueError(f"duplicate response id: {ident}")
            rows[ident] = row["answer"]
    return rows


def _validate_ids(
    expected_ids: set[str], raw: dict[str, object], *, allow_partial: bool
) -> tuple[str, ...]:
    unexpected = tuple(sorted(set(raw) - expected_ids))
    if unexpected:
        raise ValueError(f"unexpected response ids: {list(unexpected)!r}")
    missing = tuple(sorted(expected_ids - set(raw)))
    if missing and not allow_partial:
        preview = list(missing[:10])
        suffix = " ..." if len(missing) > len(preview) else ""
        raise ValueError(
            f"missing {len(missing)} of {len(expected_ids)} expected responses: "
            f"{preview!r}{suffix}; pass allow_partial=True to score missing cases as failures"
        )
    return missing


def _coverage(
    *,
    expected_n: int,
    submitted_n: int,
    parsed_n: int,
    missing: tuple[str, ...],
    parse_failures: dict[str, str],
) -> EvaluationCoverage:
    return EvaluationCoverage(
        expected_n=expected_n,
        submitted_n=submitted_n,
        parsed_n=parsed_n,
        parse_failure_n=len(parse_failures),
        missing_n=len(missing),
        submission_coverage=submitted_n / expected_n,
        parsed_coverage=parsed_n / expected_n,
        missing_ids=missing,
        parse_failures=parse_failures,
    )


def score_core_response_file(
    cases: tuple[CoreCase, ...], path: str | Path, *, allow_partial: bool = False
) -> CoreResponseReport:
    if not cases:
        raise ValueError("at least one Core case is required")
    expected = {case.id for case in cases}
    if len(expected) != len(cases):
        raise ValueError("Core case ids must be unique")
    raw = load_response_rows(path)
    missing = _validate_ids(expected, raw, allow_partial=allow_partial)
    answers: dict[str, ParsedAnswer] = {}
    failures: dict[str, str] = {}
    for ident, answer in raw.items():
        try:
            answers[ident] = parse_answer(_answer_text(answer))
        except (TypeError, ValueError) as exc:
            failures[ident] = str(exc)

    strict_passes = 0
    case_by_id = {case.id: case for case in cases}
    for ident, answer in answers.items():
        score = score_core(case_by_id[ident].hidden, answer)
        strict_passes += int(
            score.posterior_abs_error <= 0.02
            and score.provenance_abs_error == 0
            and score.choice_correct
        )
    return CoreResponseReport(
        coverage=_coverage(
            expected_n=len(cases),
            submitted_n=len(raw),
            parsed_n=len(answers),
            missing=missing,
            parse_failures=failures,
        ),
        strict_pass_rate=strict_passes / len(cases),
        parsed_summary=summarize_core(cases, answers) if answers else None,
        causal_summary=summarize_core_causal(cases, answers),
    )


def score_marketing_response_file(
    cases: tuple[MarketingCase, ...], path: str | Path, *, allow_partial: bool = False
) -> MarketingResponseReport:
    if not cases:
        raise ValueError("at least one Marketing case is required")
    expected = {case.id for case in cases}
    if len(expected) != len(cases):
        raise ValueError("Marketing case ids must be unique")
    raw = load_response_rows(path)
    missing = _validate_ids(expected, raw, allow_partial=allow_partial)
    answers: dict[str, MarketingAnswer] = {}
    failures: dict[str, str] = {}
    for ident, answer in raw.items():
        try:
            answers[ident] = parse_marketing_answer(_answer_text(answer))
        except (TypeError, ValueError) as exc:
            failures[ident] = str(exc)

    strict_passes = 0
    case_by_id = {case.id: case for case in cases}
    for ident, answer in answers.items():
        score = score_marketing(case_by_id[ident], answer)
        strict_passes += int(
            score.choice_correct
            and score.claim_audit_correct
            and score.provenance_abs_error == 0
            and not score.hard_constraint_violation
        )
    return MarketingResponseReport(
        coverage=_coverage(
            expected_n=len(cases),
            submitted_n=len(raw),
            parsed_n=len(answers),
            missing=missing,
            parse_failures=failures,
        ),
        strict_pass_rate=strict_passes / len(cases),
        parsed_summary=summarize_marketing(cases, answers) if answers else None,
    )
