---
kind: concept
---

# Homogenization

## Summary
The tendency for a single model to become the shared basis for many downstream applications — concentrating both capability and risk.

## Explanation
Described in [[Bommasani 2021]], homogenization is one of the two defining properties of [[Foundation Models]] (with [[Emergent Capabilities]]). Because many systems adapt the *same* base model via [[Pre-training and Fine-tuning]] or [[In-Context Learning]], improvements propagate widely — powerful leverage. But so do defects: bias, errors, or vulnerabilities in the base model are inherited by every downstream model, creating a single point of failure. This is why [[Alignment]] techniques like [[RLHF]] on the base model matter so much.

## Related
- [[Foundation Models]] — for which it is a defining property
- [[Emergent Capabilities]] — the other defining property of the paradigm
- [[Pre-training and Fine-tuning]] — one route by which many systems share a base
- [[In-Context Learning]] — another route by which many systems share a base
- [[Alignment]] — which matters more when one base model feeds everything
- [[RLHF]] — a way to fix the shared base once for all its uses

## Contradictions / tensions
The same shared base model that provides leverage is also the primary systemic risk. The report presents this as a tension to manage, not resolve.

## Sources
- raw/04_foundation_models.md — On the Opportunities and Risks of Foundation Models
