"""GullibleBench: epistemic robustness under manufactured consensus."""

from .generator import make_counterfactual_pair
from .oracle import bayes_posterior_b

__version__ = "1.0.0"
__all__ = ["bayes_posterior_b", "make_counterfactual_pair"]
