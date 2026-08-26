# Threat model

GullibleBench models an economically motivated information producer trying to influence an AI-mediated decision without changing the underlying product facts.

The attacker may manipulate only synthetic information presentation and topology:

- wording and omission
- unsupported marketing claims
- apparent authority
- derivative coverage
- citations and citation chains
- sponsorship/ownership relationships
- apparent source diversity
- synthetic search prominence

The attacker may **not** mutate hidden product truth, user hard requirements, source reliability parameters used by the Core oracle, or the independent primary measurement.

## Out of scope for v1

- real brand targeting
- publishing deceptive pages to the live web
- poisoning production search indexes
- impersonating real institutions
- malware or prompt-injection payloads

Keeping v1 closed and synthetic improves causal validity and prevents the benchmark itself from becoming a playbook for real-world deception.
