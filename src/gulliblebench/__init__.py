"""GullibleBench: epistemic robustness under manufactured consensus."""

from importlib.metadata import PackageNotFoundError, version

from .generator import make_counterfactual_pair
from .oracle import bayes_posterior_b

try:
    __version__ = version("gulliblebench")
except PackageNotFoundError:  # pragma: no cover - only an uninstalled source checkout
    __version__ = "0+unknown"

__all__ = ["__version__", "bayes_posterior_b", "make_counterfactual_pair"]
