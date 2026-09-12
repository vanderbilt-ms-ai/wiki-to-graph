---
kind: concept
---

# Scale and Scaling

## Summary
The observation that increasing model size, data, and compute reliably improves language-model capability — a central theme connecting [[GPT-3]] and [[Foundation Models]].

## Explanation
[[GPT-3]] operationalizes scaling: at 175B parameters it unlocks strong [[Few-Shot Learning]] and [[In-Context Learning]] not seen in smaller models. [[Foundation Models]] generalizes the point — scale is what produces [[Emergent Capabilities]] and drives [[Homogenization]] across applications. Scaling is a mechanism, not a guarantee of quality: [[RLHF]] shows that beyond a point, [[Alignment]] can matter more than additional parameters, and [[Chinchilla]] shows that *how* you scale matters — see [[Compute-Optimal Scaling]].

## Related
[[GPT-3]] · [[Few-Shot Learning]] · [[In-Context Learning]] · [[Emergent Capabilities]] · [[Foundation Models]] · [[Homogenization]] · [[RLHF]] · [[Alignment]] · [[Chinchilla]] · [[Compute-Optimal Scaling]]

## Contradictions / tensions
**"Bigger is better" is contested from two directions.**
- [[RLHF]] shows a 1.3B *aligned* model beating 175B GPT-3 on human preference — [[Alignment]] can substitute for scale.
- [[Chinchilla]] / [[Compute-Optimal Scaling]] shows GPT-3 was *undertrained*: a 70B model with more data beats it. Parameter count alone is the wrong axis; data must scale with parameters.

Together these reframe scale as necessary-but-insufficient, and specifically as *parameters-and-data-balanced-then-aligned* rather than *parameters-first*.

## Sources
- raw/03_gpt3.md (Brown et al., 2020); raw/04_foundation_models.md (Bommasani et al., 2021); raw/05_rlhf_instructgpt.md (Ouyang et al., 2022); raw/06_chinchilla.md (Hoffmann et al., 2022)
