---
kind: concept
---

# Emergent Capabilities

## Summary
Abilities that appear in large models but are absent (or much weaker) in smaller ones, arising implicitly from [[Scale and Scaling]] rather than being explicitly trained.

## Explanation
[[GPT-3]] documents emergent behaviors such as on-the-fly reasoning, 3-digit arithmetic, word unscrambling, and using novel words in a sentence — all via [[In-Context Learning]]. [[Foundation Models]] elevates *emergence* to one of the two defining properties of the paradigm (alongside [[Homogenization]]), noting that because these capabilities are emergent, we often lack a clear understanding of how the models work, when they fail, or what they can do.

## Related
[[GPT-3]] · [[Scale and Scaling]] · [[In-Context Learning]] · [[Few-Shot Learning]] · [[Foundation Models]] · [[Homogenization]] · [[Compute-Optimal Scaling]] · [[Chinchilla]]

## Contradictions / tensions
- Emergence is presented as powerful but poorly understood: [[Foundation Models]] frames the same unpredictability as a *risk*, whereas [[GPT-3]] frames emergent few-shot ability mainly as a *capability*.
- [[Compute-Optimal Scaling]] complicates the simple "capability emerges from parameter count" story: [[Chinchilla]] shows capability depends on training tokens as much as size, so emergence tracks *compute-optimal* scale, not raw parameters.

## Sources
- raw/03_gpt3.md (Brown et al., 2020); raw/04_foundation_models.md (Bommasani et al., 2021)
