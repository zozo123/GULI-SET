import pytest

from gulliblebench.flipcost import FlipPredicate, flip_cost
from gulliblebench.marketing import generate_marketing_suite

inspect_ai = pytest.importorskip("inspect_ai", reason="optional [inspect] extra not installed")


def _tasks():
    from gulliblebench import inspect_tasks

    return inspect_tasks


def test_every_task_constructs_with_the_expected_sample_count() -> None:
    tasks = _tasks()
    assert len(tasks.core().dataset) == 48
    assert len(tasks.marketing().dataset) == 64
    assert len(tasks.marketing_agent().dataset) == 64
    assert len(tasks.marketing_agent_attacked().dataset) == 64


def test_attacked_task_defaults_to_no_purchased_action() -> None:
    sample = _tasks().marketing_agent_attacked().dataset[0]
    assert sample.metadata["attacker_plan"] == "no action"
    assert sample.metadata["attacker_cost"] == 0


def test_attacked_task_reports_plan_cost_from_the_frozen_price_table() -> None:
    sample = _tasks().marketing_agent_attacked(echo=6, forge_measurement=1).dataset[0]
    assert sample.metadata["attacker_plan"] == "6xecho + 1xforge_measurement"
    assert sample.metadata["attacker_cost"] == 6 * 1 + 1 * 8


def test_reference_flip_cost_is_measured_on_the_pristine_case() -> None:
    """The reference must be comparable to the ladder, not the cost remaining after the plan."""

    from gulliblebench.flipcost import READER_LADDER

    reader = READER_LADDER[-1]
    pristine = {case.id: case for case in generate_marketing_suite()}
    for sample in _tasks().marketing_agent_attacked(echo=6).dataset:
        expected = flip_cost(
            pristine[str(sample.id)], reader, predicate=FlipPredicate.CHOICE, max_budget=16
        ).cost
        assert sample.metadata["reference_flip_cost_choice"] == expected
        assert sample.metadata["reference_reader"] == reader.name


def test_attack_reaches_the_synthetic_web_but_not_the_prompt_or_the_case_set() -> None:
    """The purchased pages must exist in the searchable web, not in the task prompt.

    The agent prompt is deliberately page-free: the whole point of the agent track is
    that evidence is reached through search, so an attack that only edited the prompt
    would not be measuring bounded attention at all.
    """

    from gulliblebench.flipcost import AttackerPlan, apply_plan
    from gulliblebench.synthetic_web import SyntheticWeb

    tasks = _tasks()
    unattacked = {str(s.id): s for s in tasks.marketing_agent().dataset}
    attacked = {str(s.id): s for s in tasks.marketing_agent_attacked(echo=9).dataset}

    assert set(unattacked) == set(attacked)
    for ident, sample in attacked.items():
        assert sample.input == unattacked[ident].input

    case = generate_marketing_suite()[0]
    grown = apply_plan(case, AttackerPlan(echo=9))
    assert len(SyntheticWeb(grown).search("latency", limit=50)) == len(case.pages) + 9
