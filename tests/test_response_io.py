import json

from gulliblebench.dataset import generate_core_suite
from gulliblebench.response_io import score_core_response_file


def test_score_response_file(tmp_path) -> None:
    case = generate_core_suite(page_counts=(1,), reliabilities=(0.75,))[0]
    row = {
        "id": case.id,
        "answer": {"probability_b": 0.25, "independent_evidence_units": 1, "choice": "A"},
    }
    path = tmp_path / "responses.jsonl"
    path.write_text(json.dumps(row) + "\n")
    summary = score_core_response_file((case,), path)
    assert summary.strict_pass_rate == 1.0
