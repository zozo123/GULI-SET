from math import isclose

import pytest

from gulliblebench.oracle import bayes_posterior_b
from gulliblebench.world import EvidenceOrigin, Side


def test_one_75pct_source_gives_75pct_posterior() -> None:
    assert isclose(bayes_posterior_b(0.5, (EvidenceOrigin("o1", Side.B, 0.75),)), 0.75)


def test_four_independent_75pct_sources() -> None:
    origins = tuple(EvidenceOrigin(f"o{i}", Side.B, 0.75) for i in range(4))
    assert isclose(bayes_posterior_b(0.5, origins), 81 / 82)


def test_duplicate_origins_rejected() -> None:
    with pytest.raises(ValueError):
        bayes_posterior_b(
            0.5, (EvidenceOrigin("x", Side.B, 0.75), EvidenceOrigin("x", Side.B, 0.75))
        )
