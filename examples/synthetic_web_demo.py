from gulliblebench.marketing import MarketingAttack, make_marketing_case
from gulliblebench.synthetic_web import SyntheticWeb
from gulliblebench.world import Side

case = make_marketing_case(0, MarketingAttack.FULL_STACK, target_side=Side.B)
web = SyntheticWeb(case)
print(case.campaign_claim)
for result in web.search("Nova performance latency", limit=5):
    print(f"{result.score:.2f} {result.source}: {result.url}")
print("\nTop page:\n", web.open(web.search("Nova performance latency")[0].url).text)
