from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .dataset import generate_core_suite
from .evaluate import deterministic_baseline_results, flip_cost_ladder_results
from .flipcost import FlipPredicate
from .marketing import generate_marketing_suite
from .marketing_serialization import export_agent_jsonl, export_marketing_jsonl
from .meta_harness import load_demo_cases, meta_demo_to_dict, render_meta_demo, run_meta_demo
from .reporting import (
    dump_json,
    render_flip_cost_ladder,
    render_web_query,
    write_baseline_markdown,
    write_flip_cost_markdown,
)
from .response_io import score_core_response_file, score_marketing_response_file
from .serialization import export_core_jsonl, export_hidden_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(prog="gulliblebench")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("generate-all", help="generate Core and Marketing v1 datasets")
    sub.add_parser("baselines", help="run deterministic oracle and gullible baselines")
    score_core = sub.add_parser("score-core", help="score a Core response JSONL file")
    score_core.add_argument("responses")
    score_core.add_argument(
        "--allow-partial",
        action="store_true",
        help="allow missing ids but count them as failures (default: reject incomplete files)",
    )
    score_marketing = sub.add_parser(
        "score-marketing", help="score a Marketing response JSONL file"
    )
    score_marketing.add_argument("responses")
    score_marketing.add_argument(
        "--allow-partial",
        action="store_true",
        help="allow missing ids but count them as failures (default: reject incomplete files)",
    )
    web = sub.add_parser(
        "web", help="query the closed synthetic web from a shell (for terminal agents)"
    )
    web.add_argument("action", choices=["search", "open"])
    web.add_argument("query", help="search terms, or the exact synthetic URL to open")
    web.add_argument("--case", required=True, help="marketing case id, e.g. from data/agent.jsonl")
    web.add_argument("--limit", type=int, default=5, help="results to return (search only)")
    web.add_argument(
        "--attacker-plan",
        help="apply purchased attacker actions before serving, as name=count pairs "
        "(e.g. 'echo=6,seo_boost=1'). Used to measure empirical Flip Cost.",
    )
    flip = sub.add_parser(
        "flip-cost", help="compute exact Flip Cost for the synthetic-web reader ladder"
    )
    flip.add_argument(
        "--max-budget", type=int, default=16, help="attacker budget cap (default: 16)"
    )
    flip.add_argument(
        "--predicate",
        choices=[p.value for p in FlipPredicate],
        help="print only this flip predicate (default: all)",
    )
    flip.add_argument("--json", action="store_true", help="emit the full ladder artifact as JSON")
    demo = sub.add_parser("demo", help="run the zero-API Meta-harness demonstration")
    demo.add_argument("--data", help="path to a small demo recipe JSON file")
    demo.add_argument("--max-depth", type=int, default=6, help="maximum number of meta-layers")
    demo.add_argument("--json", action="store_true", help="emit the full run artifact as JSON")
    args = parser.parse_args()

    if args.command == "generate-all":
        core = generate_core_suite()
        marketing = generate_marketing_suite()
        export_core_jsonl(core, "data/core.jsonl")
        export_hidden_jsonl(core, "data/core-hidden.jsonl")
        export_marketing_jsonl(marketing, "data/marketing-neutral.jsonl")
        export_marketing_jsonl(marketing, "data/marketing-defensive.jsonl", defensive=True)
        export_marketing_jsonl(marketing, "data/marketing-hidden.jsonl", hidden=True)
        export_agent_jsonl(marketing, "data/agent.jsonl")
        print(f"generated {len(core)} Core and {len(marketing)} Marketing cases")
    elif args.command == "baselines":
        core = generate_core_suite()
        marketing = generate_marketing_suite()
        results = deterministic_baseline_results(core, marketing)
        dump_json(results, "results/deterministic-baselines.json")
        write_baseline_markdown(results, "results/DETERMINISTIC_BASELINES.md")
        for name, tracks in results.items():
            print(name, tracks)
    elif args.command == "score-core":
        core = generate_core_suite()
        print(
            json.dumps(
                asdict(
                    score_core_response_file(
                        core, args.responses, allow_partial=args.allow_partial
                    )
                ),
                indent=2,
            )
        )
    elif args.command == "score-marketing":
        marketing = generate_marketing_suite()
        print(
            json.dumps(
                asdict(
                    score_marketing_response_file(
                        marketing, args.responses, allow_partial=args.allow_partial
                    )
                ),
                indent=2,
            )
        )
    elif args.command == "web":
        print(
            render_web_query(
                case_id=args.case,
                action=args.action,
                query=args.query,
                limit=args.limit,
                attacker_plan=args.attacker_plan,
            )
        )
    elif args.command == "flip-cost":
        marketing = generate_marketing_suite()
        results = flip_cost_ladder_results(marketing, max_budget=args.max_budget)
        dump_json(results, "results/flip-cost.json")
        write_flip_cost_markdown(results, "results/FLIP_COST.md")
        if args.json:
            print(json.dumps(results, indent=2, sort_keys=True))
        else:
            print(render_flip_cost_ladder(results, predicate=args.predicate))
    elif args.command == "demo":
        cases = load_demo_cases(args.data) if args.data else load_demo_cases()
        run = run_meta_demo(cases, max_depth=args.max_depth)
        if args.json:
            print(json.dumps(meta_demo_to_dict(run), indent=2))
        else:
            print(render_meta_demo(run))


if __name__ == "__main__":
    main()
