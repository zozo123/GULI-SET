from gulliblebench.generator import make_counterfactual_pair
from gulliblebench.oracle import bayes_posterior_b

echo, independent = make_counterfactual_pair(n_pages=4, reliability=0.75)
print("echo       ", bayes_posterior_b(echo.prior_b, echo.evidence_origins))
print("independent", bayes_posterior_b(independent.prior_b, independent.evidence_origins))
