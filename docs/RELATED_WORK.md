# Related work and novelty boundary

This file records the closest work checked during the v1.0 design freeze.

## SafeGEO (2026)

SafeGEO evaluates Generative Engine Optimization attacks on LLM recommendation agents: 22 attack packages plus truthful controls over 600 cases. It shows seller-controlled source rewriting can substantially promote flawed products and evaluates agent-side mitigations.

Paper: https://arxiv.org/abs/2606.28356
Code: https://github.com/QianfengWen/SafeGEO

**Boundary:** GullibleBench makes the *dependency structure among apparently distinct sources* a controlled experimental variable and couples it to an exact evidence oracle.

## Bias Beware (EMNLP 2025)

Filandrianos et al. study cognitive biases as black-box attacks on LLM product recommendation and show, among other effects, that social proof can increase recommendation visibility.

https://aclanthology.org/2025.emnlp-main.1140/

**Boundary:** GullibleBench is not primarily a cognitive-bias phrasing benchmark; it studies evidentiary independence and provenance topology.

## Whose Facts Win? (ACL 2026)

Schuster, Gautam, and Markert study source preferences under knowledge conflict and show repetition can reverse source-credibility preferences.

https://aclanthology.org/2026.acl-long.1357/

**Boundary:** repetition alone is not GullibleBench's novelty claim. The benchmark explicitly contrasts repeated/derivative evidence with genuinely independent evidence under a known causal process and follows the effect into downstream decisions.

## CONFACT (IJCAI 2025)

CONFACT studies retrieval-augmented fact checking with conflicting evidence and source credibility.

https://www.ijcai.org/proceedings/2025/1073

**Boundary:** GullibleBench controls the provenance DAG and source dependence itself, including manufactured consensus and marketing ecosystems.

## Inspect AI

Inspect AI provides datasets, solvers, scorers, model providers, custom tools, repeated evaluation, and offline scoring. GullibleBench uses it as an optional execution harness rather than reimplementing provider orchestration.

https://inspect.aisi.org.uk/
