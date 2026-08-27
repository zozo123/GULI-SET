from __future__ import annotations

import json

import pytest

from gulliblebench.baselines import oracle_marketing_answer
from gulliblebench.dataset import generate_core_suite
from gulliblebench.marketing import generate_marketing_suite
from gulliblebench.response_io import (
    score_core_response_file,
    score_marketing_response_file,
)


def _write(path, rows: list[dict[str, object]]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))


def test_score_complete_response_file(tmp_path) -> None:
    case = generate_core_suite(page_counts=(1,), reliabilities=(0.75,))[0]
    path = tmp_path / "responses.jsonl"
    _write(
        path,
        [
            {
                "id": case.id,
                "answer": {
                    "probability_b": 0.25,
                    "independent_evidence_units": 1,
                    "choice": "A",
                },
            }
        ],
    )
    report = score_core_response_file((case,), path)
    assert report.strict_pass_rate == 1.0
    assert report.coverage.expected_n == report.coverage.parsed_n == 1
    assert report.coverage.parsed_coverage == 1.0
    assert report.parsed_summary is not None
    assert report.causal_summary.expected_pairs == 0


def test_missing_responses_fail_closed_by_default(tmp_path) -> None:
    cases = generate_core_suite(page_counts=(1,), reliabilities=(0.75,))
    path = tmp_path / "responses.jsonl"
    _write(path, [])
    with pytest.raises(ValueError, match="missing 4 of 4 expected responses"):
        score_core_response_file(cases, path)


def test_allow_partial_keeps_full_suite_denominator(tmp_path) -> None:
    cases = generate_core_suite(page_counts=(1,), reliabilities=(0.75,))
    case = cases[0]
    path = tmp_path / "responses.jsonl"
    _write(
        path,
        [
            {
                "id": case.id,
                "answer": {
                    "probability_b": 0.25,
                    "independent_evidence_units": 1,
                    "choice": "A",
                },
            }
        ],
    )
    report = score_core_response_file(cases, path, allow_partial=True)
    assert report.coverage.submitted_n == report.coverage.parsed_n == 1
    assert report.coverage.missing_n == 3
    assert report.coverage.submission_coverage == 0.25
    assert report.parsed_summary is not None
    assert report.parsed_summary.strict_pass_rate == 1.0  # conditional, named as such
    assert report.strict_pass_rate == 0.25  # the publishable full-denominator rate


def test_unknown_ids_are_never_silently_ignored(tmp_path) -> None:
    cases = generate_core_suite(page_counts=(1,), reliabilities=(0.75,))
    path = tmp_path / "responses.jsonl"
    _write(path, [{"id": "not-a-benchmark-case", "answer": {}}])
    with pytest.raises(ValueError, match="unexpected response ids"):
        score_core_response_file(cases, path, allow_partial=True)


def test_parse_failures_are_counted_not_dropped(tmp_path) -> None:
    case = generate_core_suite(page_counts=(1,), reliabilities=(0.75,))[0]
    path = tmp_path / "responses.jsonl"
    _write(path, [{"id": case.id, "answer": "not JSON"}])
    report = score_core_response_file((case,), path)
    assert report.coverage.submitted_n == 1
    assert report.coverage.parsed_n == 0
    assert report.coverage.parse_failure_n == 1
    assert report.coverage.parsed_coverage == 0.0
    assert case.id in report.coverage.parse_failures
    assert report.parsed_summary is None
    assert report.strict_pass_rate == 0.0


def test_marketing_report_uses_same_fail_closed_contract(tmp_path) -> None:
    cases = generate_marketing_suite(1)
    rows = []
    for case in cases:
        answer = oracle_marketing_answer(case)
        rows.append(
            {
                "id": case.id,
                "answer": {
                    "choice": answer.choice.value,
                    "campaign_claim_supported": answer.campaign_claim_supported,
                    "independent_supporting_origins": answer.independent_supporting_origins,
                },
            }
        )
    path = tmp_path / "responses.jsonl"
    _write(path, rows)
    report = score_marketing_response_file(cases, path)
    assert report.coverage.parsed_coverage == 1.0
    assert report.strict_pass_rate == 1.0

    _write(path, rows[:-1])
    with pytest.raises(ValueError, match="missing 1 of 8 expected responses"):
        score_marketing_response_file(cases, path)
