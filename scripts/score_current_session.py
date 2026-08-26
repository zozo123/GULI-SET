import json
from dataclasses import asdict
from gulliblebench.dataset import generate_core_suite
from gulliblebench.evaluate import summarize_core, summarize_marketing
from gulliblebench.marketing import generate_marketing_suite
from gulliblebench.marketing_scoring import MarketingAnswer
from gulliblebench.scoring import ParsedAnswer
from gulliblebench.world import Side

payload = json.load(open('results/gpt-5.6-sol-current-session-responses.json'))
core_cases = generate_core_suite()
market_cases = generate_marketing_suite()
core_answers = {k: ParsedAnswer(v['probability_b'], v['independent_evidence_units'], Side(v['choice'])) for k,v in payload['core'].items()}
market_answers = {k: MarketingAnswer(Side(v['choice']), v['campaign_claim_supported'], v['independent_supporting_origins']) for k,v in payload['marketing'].items()}
summary = {
    'model': payload['model'],
    'evaluation_mode': payload['evaluation_mode'],
    'blind': payload['blind'],
    'contaminated': payload['contaminated'],
    'leaderboard_eligible': payload['leaderboard_eligible'],
    'core': asdict(summarize_core(core_cases, core_answers)),
    'marketing': asdict(summarize_marketing(market_cases, market_answers)),
}
json.dump(summary, open('results/gpt-5.6-sol-current-session-summary.json','w'), indent=2, sort_keys=True)
print(json.dumps(summary, indent=2, sort_keys=True))
