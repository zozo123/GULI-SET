from pathlib import Path

from gulliblebench.meta_harness import (
    FrozenOmega,
    load_demo_cases,
    meta_demo_to_dict,
    render_meta_demo,
    run_meta_demo,
)

ROOT = Path(__file__).resolve().parents[1]


def test_tiny_recipe_expands_into_real_marketing_cases() -> None:
    cases = load_demo_cases(ROOT / "data" / "demo.json")
    default_cases = load_demo_cases()
    assert len(cases) == 4
    assert [case.id for case in default_cases] == [case.id for case in cases]
    assert cases[0].attack.value == "plain_false"
    assert cases[-1].attack.value == "circular_citation"


def test_frozen_omega_builds_expected_stack_and_converges() -> None:
    cases = load_demo_cases(ROOT / "data" / "demo.json")
    run = run_meta_demo(cases, omega=FrozenOmega())

    assert [snapshot.depth for snapshot in run.snapshots] == [0, 1, 2, 3]
    assert run.snapshots[0].summary.strict_pass_rate < 1.0
    assert run.snapshots[2].summary.hard_constraint_violation_rate == 0.0
    assert run.snapshots[-1].summary.strict_pass_rate == 1.0
    assert [layer.name for layer in run.snapshots[-1].stack] == [
        "collapse_provenance",
        "guard_constraints",
        "verify_independence",
    ]
    assert run.convergence_reason == "no scored failures remain"


def test_demo_outputs_are_serializable_and_readable() -> None:
    run = run_meta_demo(load_demo_cases(ROOT / "data" / "demo.json"))
    payload = meta_demo_to_dict(run)
    rendered = render_meta_demo(run)

    assert payload["snapshots"][-1]["summary"]["strict_pass_rate"] == 1.0
    assert "GULI-SET // META HARNESS" in rendered
    assert "compression -> routing -> verification" in rendered
