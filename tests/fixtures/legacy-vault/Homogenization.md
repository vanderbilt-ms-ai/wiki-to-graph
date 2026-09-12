---
kind: concept
---

# Homogenization

## Summary
The tendency, described in *Foundation Models*, for a single model to become the shared basis for many downstream applications — concentrating both capability and risk.

## Explanation
Homogenization is one of the two defining properties of [[Foundation Models]] (with [[Emergent Capabilities]]). Because many systems adapt the *same* base model via [[Pre-training and Fine-tuning]] or [[In-Context Learning]], improvements propagate widely — powerful leverage. But so do defects: bias, errors, or vulnerabilities in the base model are inherited by every downstream model, creating a single point of failure. This is why [[Alignment]] techniques like [[RLHF]] on the base model matter so much.

## Related
[[Foundation Models]] · [[Emergent Capabilities]] · [[Pre-training and Fine-tuning]] · [[In-Context Learning]] · [[Alignment]] · [[RLHF]]

## Contradictions / tensions
Inherent double edge: the same property that provides leverage (shared base model) is also the primary systemic risk. The report presents this as a tension to manage, not resolve.

## Sources
- raw/04_foundation_models.md (Bommasani et al., 2021)
