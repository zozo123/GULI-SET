import pytest

from gulliblebench.marketing import MarketingAttack, make_marketing_case
from gulliblebench.synthetic_web import SyntheticWeb
from gulliblebench.world import Side


def test_search_is_deterministic_and_open_roundtrips() -> None:
    case = make_marketing_case(0, MarketingAttack.FULL_STACK, target_side=Side.B)
    web = SyntheticWeb(case)
    a = web.search("Nova performance latency")
    b = web.search("Nova performance latency")
    assert a == b
    assert web.open(a[0].url).url == a[0].url


def test_unknown_url_rejected() -> None:
    web = SyntheticWeb(make_marketing_case(0, MarketingAttack.PLAIN_FALSE, target_side=Side.B))
    with pytest.raises(KeyError):
        web.open("https://missing.test/nope")
