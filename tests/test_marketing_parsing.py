import pytest

from gulliblebench.marketing_scoring import parse_marketing_answer
from gulliblebench.world import Side


def test_parse_marketing() -> None:
    a = parse_marketing_answer(
        '{"choice":"A","campaign_claim_supported":false,"independent_supporting_origins":0}'
    )
    assert a.choice is Side.A


def test_parse_marketing_bad_bool() -> None:
    with pytest.raises(ValueError):
        parse_marketing_answer(
            '{"choice":"A","campaign_claim_supported":"no","independent_supporting_origins":0}'
        )
