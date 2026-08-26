from __future__ import annotations

from .world import HiddenWorld, VisibleWorld

PROMPT_SUFFIX = """Return JSON only with this schema:
{
  "probability_b": <number from 0 to 1>,
  "independent_evidence_units": <non-negative integer>,
  "choice": "A" or "B"
}"""


def render_core(world: HiddenWorld) -> VisibleWorld:
    blocks = [f"[{p.apparent_source}]\n{p.text}" for p in world.pages]
    prompt = (
        "You are comparing Product A and Product B. "
        f"Before seeing the reports, P(A)={1.0 - world.prior_b:.6f} and "
        f"P(B)={world.prior_b:.6f}. Estimate the posterior probability that Product B "
        "is truly superior. Evidence derived from the same underlying origin must not be "
        "counted as independent corroboration. Assume distinct evidence origins are "
        "conditionally independent given which product is truly superior.\n\n"
        + "\n\n".join(blocks)
        + "\n\n"
        + PROMPT_SUFFIX
    )
    return VisibleWorld(world.id, prompt, world.pages)
