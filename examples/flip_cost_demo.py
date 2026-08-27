"""Flip Cost on one case: what the reader reads, and what it costs to flip it."""

from __future__ import annotations

from gulliblebench.flipcost import (
    QUERY_GENERAL,
    READER_LADDER,
    AttackerPlan,
    FlipPredicate,
    ReaderPolicy,
    apply_plan,
    flip_cost,
)
from gulliblebench.marketing import (
    MarketingAttack,
    MarketingCase,
    MarketingPage,
    make_marketing_case,
)
from gulliblebench.synthetic_web import SyntheticWeb
from gulliblebench.world import Side

MAX_BUDGET = 16


def page_kind(page: MarketingPage) -> str:
    if page.independent_measurement:
        return "primary measurement"
    if not page.supports_campaign_claim:
        return "refuting page"
    return "echo of vendor claim" if page.cites else "vendor claim"


def verdict(case: MarketingCase, choice: Side) -> str:
    product = next(p for p in case.products if p.side is choice)
    mark = "correct" if choice is case.correct_side else "wrong"
    return f"{choice.value} {product.name} ({mark})"


def cell(cost: int | None) -> str:
    return "-" if cost is None else str(cost)


case = make_marketing_case(0, MarketingAttack.MANUFACTURED_CONSENSUS, target_side=Side.B)
web = SyntheticWeb(case)
product_a, product_b = case.products
query = QUERY_GENERAL.format(a=product_a.name, b=product_b.name)
base: ReaderPolicy = READER_LADDER[0]

print("GULI-SET // FLIP COST")
print(f"case {case.id} · max_budget={MAX_BUDGET}")
print()
print(f"campaign claim: {case.campaign_claim}")
print(
    f"ground truth:   {product_a.name} measures {product_a.latency_ms} ms, "
    f"{product_b.name} measures {product_b.latency_ms} ms, "
    f"requirement <= {case.requirement_latency_ms} ms"
)
print()

read_urls = {page.url for page in base.read(case)}
print(f'{len(case.pages)} pages exist. Ranked for the reader query "{query}":')
print()
print("rank  score  source                kind                  read by base reader")
print("----  -----  --------------------  --------------------  -------------------")
for rank, result in enumerate(web.search(query, limit=len(case.pages)), 1):
    page = web.open(result.url)
    opened = "yes" if result.url in read_urls else "no"
    print(
        f"{rank:>4}  {result.score:>5.2f}  {result.source:<20}  "
        f"{page_kind(page):<20}  {opened}"
    )
print()
print(
    f"{base.name} opens {len(read_urls)} of {len(case.pages)} pages "
    f"(read_limit={base.read_limit}) and never sees the only primary measurement."
)
print(
    f"It answers {verdict(case, base.answer(case).choice)} "
    "before the attacker has spent anything."
)
print()

print(f"Minimal attacker plan per rung (predicate={FlipPredicate.CHOICE.value}):")
print()
print("rung  reader                  pages read  pre-attack answer      cost  minimal plan")
print("----  ----------------------  ----------  ---------------------  ----  ------------")
rows = []
for rung, reader in enumerate(READER_LADDER):
    pages_read = len(reader.read(case))
    costs = {
        predicate: flip_cost(case, reader, predicate=predicate, max_budget=MAX_BUDGET)
        for predicate in FlipPredicate
    }
    choice_result = costs[FlipPredicate.CHOICE]
    rows.append((rung, reader, pages_read, costs))
    print(
        f"{rung:>4}  {reader.name:<22}  {pages_read:>4} / {len(case.pages):<3}  "
        f"{verdict(case, reader.answer(case).choice):<21}  "
        f"{cell(choice_result.cost):>4}  {choice_result.plan}"
    )
print()

winner = AttackerPlan(echo=6)
attacked = apply_plan(case, winner)
top = READER_LADDER[-1]
print(
    f"Against the top rung the minimal plan is {winner.describe()}, cost {winner.cost}:"
)
print(
    f"the web grows from {len(case.pages)} to {len(attacked.pages)} pages, past the "
    f"reader's ceiling of {top.max_reads} reads, so it opens {len(top.read(attacked))}"
)
print(
    "pages and the lab measurement is off the end again. Answer: "
    f"{verdict(attacked, top.answer(attacked).choice)}."
)
print()
print("launder and bury_lab are never cost-optimal here: echo buys volume and rank at")
print("cost 1, and demoting the lab changes nothing while the whole web still fits")
print("inside the escalating reader's ceiling.")
print()

print("Flip Cost ladder (exact minimum budget, - means not flippable within the cap):")
print()
print("rung  reader                  choice  audit  provenance")
print("----  ----------------------  ------  -----  ----------")
for rung, reader, _pages_read, costs in rows:
    print(
        f"{rung:>4}  {reader.name:<22}  "
        f"{cell(costs[FlipPredicate.CHOICE].cost):>6}  "
        f"{cell(costs[FlipPredicate.AUDIT].cost):>5}  "
        f"{cell(costs[FlipPredicate.PROVENANCE].cost):>10}"
    )
