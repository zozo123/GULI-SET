# The GULI-SET Meta harness

## Purpose

The harness makes one abstract process-improvement idea visible in under a second:

> keep the improver fixed; give it a growing record of traces and installed layers; stop when another layer is no longer useful.

It connects that loop to GullibleBench's real marketing generator and exact scorer. The run is deterministic and needs no model, API key, network, or LLM judge.

## End-to-end path

1. `data/demo.json` selects four attack families from one seeded synthetic world.
2. The normal marketing generator expands that tiny recipe into `MarketingCase` objects.
3. The base solver runs the existing deliberately gullible page-counting policy.
4. The existing marketing scorer emits per-case failure traces and aggregate metrics.
5. One unchanged `FrozenOmega` reads the full history plus the installed stack.
6. Omega returns one typed layer or converges.
7. The full stack runs again on every case.

The word *typed* matters: layers come from a small audited registry. The demo never executes generated text or dynamically evaluates code.

## What grows

At depth 0, Omega sees four fresh traces. At later depths it sees all prior traces plus the layer stack:

| Depth | New role | Trigger | Observable effect |
|---:|---|---|---|
| 0 | base page counter | none | derivative pages dominate three of four cases |
| 1 | compression | provenance MAE > 1 | repeated roots collapse; MAE 3.25 → 0.75 |
| 2 | routing | any hard violation | measured requirements override popularity; safe choices reach 100% |
| 3 | verification | audit/provenance failure remains | only independent measurements support the claim; strict pass reaches 100% |

The roles are not labels supplied by the recipe. They are properties of the layer selected from the observed failure signature. Depth is not preset to three; the run stops because Omega has no remaining scored failure to address.

## What each layer can see

- `collapse_provenance` uses the benchmark's explicit synthetic root annotations.
- `guard_constraints` extracts latency measurements from rendered page text and combines them with the user's price and encryption requirements. It does not read the target answer.
- `verify_independence` uses the synthetic independent-measurement annotation and supporting/refuting direction.

These annotations make the demo auditable. They also make it unsuitable as a blind model result. Model-facing datasets omit hidden campaign provenance, and the agent track hides pages behind the local `search()` and `open()` tools.

## Relation to Meta\(^n\)

[Meta\(^n\)](https://arxiv.org/abs/2608.24735) describes a fixed meta-operation that consumes traces and the code stack below it, then produces a new pre-process hook and callable helper library. Its [official repository](https://github.com/minnesotanlp/meta-n) includes LLM-generated layers and evolutionary archive search.

GULI-SET borrows only the compact control pattern needed for a reliable demonstration:

| Capability | This demo | Official Meta\(^n\) system |
|---|---|---|
| Fixed improver | yes | yes |
| Growing trace + stack input | yes | yes |
| Emergent stopping depth | yes | yes |
| Generated executable helpers | no; audited registry only | yes |
| Evolutionary archive | no | yes |
| Evidence of model self-improvement | no | evaluated in the paper |

The harness therefore demonstrates orchestration and scoring, not a reproduction or empirical validation of the paper.

## Commands

```bash
gulliblebench demo
gulliblebench demo --json
gulliblebench demo --data path/to/recipe.json --max-depth 6
```

The JSON mode includes every per-case trace, every installed layer with its rationale, aggregate summaries, context growth, and the convergence reason.

## Extending it safely

Add cases by copying `data/demo.json` and listing more `MarketingAttack` values. Add a process rule by defining a `PolicyLayer`, implementing its pure transformation in `solve_with_stack`, and adding an evidence-backed selection condition to `FrozenOmega.propose`. Then add a regression test that proves both the intended improvement and convergence.
