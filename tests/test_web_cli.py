"""The shell-facing synthetic web must expose exactly what a model may see, and no more."""

from __future__ import annotations

import pytest

from gulliblebench.flipcost import AttackerPlan
from gulliblebench.marketing import generate_marketing_suite
from gulliblebench.reporting import parse_attacker_plan, render_web_query

CASE = "marketing-00-manufactured_consensus-targetB"
QUERY = "Nova Atlas latency performance"


def test_search_is_deterministic_and_respects_limit() -> None:
    first = render_web_query(case_id=CASE, action="search", query=QUERY, limit=3)
    second = render_web_query(case_id=CASE, action="search", query=QUERY, limit=3)
    assert first == second
    assert len(first.splitlines()) == 3


def test_open_returns_only_model_visible_fields() -> None:
    """Hidden provenance annotations must never reach a model through this interface."""

    case = next(c for c in generate_marketing_suite() if c.id == CASE)
    for page in case.pages:
        rendered = render_web_query(case_id=CASE, action="open", query=page.url)
        assert page.source in rendered
        assert page.url in rendered
        assert page.text in rendered
        for hidden in ("root_origin", "independent_measurement", "supports_campaign_claim"):
            assert hidden not in rendered
        assert page.root_origin not in rendered


def test_open_emits_exactly_the_four_visible_fields_and_nothing_else() -> None:
    """Pinned byte-for-byte, so adding any field to the page render fails here first.

    A substring check for the answer key would be worthless: ``correct_side`` renders as the
    single letter "A", which occurs in ordinary prose. Asserting the complete output instead
    catches a leak of any kind.
    """

    case = next(c for c in generate_marketing_suite() if c.id == CASE)
    for page in case.pages:
        cites = ", ".join(page.cites) if page.cites else "none"
        expected = f"Source: {page.source}\nURL: {page.url}\n{page.text}\nCites: {cites}"
        assert render_web_query(case_id=CASE, action="open", query=page.url) == expected


def test_attacker_plan_pushes_the_primary_measurement_out_of_reach() -> None:
    """The whole agent-track premise: purchased volume can bury the decisive page."""

    lab_url = next(
        page.url
        for page in next(c for c in generate_marketing_suite() if c.id == CASE).pages
        if page.independent_measurement
    )
    pristine = render_web_query(case_id=CASE, action="search", query=QUERY, limit=7)
    attacked = render_web_query(
        case_id=CASE, action="search", query=QUERY, limit=7, attacker_plan="echo=6"
    )
    assert lab_url in pristine
    assert lab_url not in attacked


def test_unknown_case_and_url_are_rejected() -> None:
    with pytest.raises(ValueError):
        render_web_query(case_id="no-such-case", action="search", query=QUERY)
    with pytest.raises(KeyError):
        render_web_query(case_id=CASE, action="open", query="https://missing.test/nope")


@pytest.mark.parametrize(
    ("spec", "expected"),
    [
        (None, AttackerPlan()),
        ("", AttackerPlan()),
        ("echo=6", AttackerPlan(echo=6)),
        ("echo=2,seo_boost=1", AttackerPlan(echo=2, seo_boost=1)),
        (" echo = 2 , forge_measurement = 1 ", AttackerPlan(echo=2, forge_measurement=1)),
    ],
)
def test_parse_attacker_plan_accepts_valid_specs(spec: str | None, expected: AttackerPlan) -> None:
    assert parse_attacker_plan(spec) == expected


@pytest.mark.parametrize("spec", ["echo", "echo=x", "nonsense=1", "echo=-1"])
def test_parse_attacker_plan_rejects_invalid_specs(spec: str) -> None:
    with pytest.raises(ValueError):
        parse_attacker_plan(spec)
