---
kind: concept
---

# Scale and Scaling

## Summary
The observation that increasing model size, data, and compute reliably improves language-model capability — a central theme connecting [[GPT-3]] and [[Foundation Models]].

## Explanation
[[Brown 2020]] operationalizes scaling: at 175B parameters [[GPT-3]] unlocks strong [[Few-Shot Learning]] and [[In-Context Learning]] not seen in smaller models. [[Bommasani 2021]] generalizes the point — scale is what produces [[Emergent Capabilities]] and drives [[Homogenization]] across [[Foundation Models]]. Scaling is a mechanism, not a guarantee of quality: [[Ouyang 2022]] shows through [[RLHF]] that beyond a point, [[Alignment]] can matter more than additional parameters, and [[Hoffmann 2022]] shows through [[Chinchilla]] that *how* you scale matters — see [[Compute-Optimal Scaling]].

## Related
- [[GPT-3]] — the model that operationalizes scaling
- [[Few-Shot Learning]] — an ability that improves with size
- [[In-Context Learning]] — an ability that appears with size
- [[Emergent Capabilities]] — what scale is said to produce
- [[Foundation Models]] — the paradigm scale defines
- [[Homogenization]] — which scale drives across applications
- [[RLHF]] — evidence that alignment can outweigh size
- [[Alignment]] — the lever weighed against size
- [[Chinchilla]] — evidence that data must grow with size
- [[Compute-Optimal Scaling]] — the principle for scaling efficiently

## Contradictions / tensions
**"Bigger is better" is contested from two directions.**
- [[RLHF]] — a 1.3B aligned model beats the 175B GPT-3 on human preference, so alignment can substitute for scale.
- [[Chinchilla]] — GPT-3 was undertrained and a 70B model with more data beats it, so parameter count alone is the wrong axis.

Together these reframe scale as necessary-but-insufficient: parameters and data balanced, then aligned, rather than parameters first.

## Sources
- raw/03_gpt3.md — Language Models are Few-Shot Learners
- raw/04_foundation_models.md — On the Opportunities and Risks of Foundation Models
- raw/05_rlhf_instructgpt.md — Training Language Models to Follow Instructions with Human Feedback
- raw/06_chinchilla.md — Training Compute-Optimal Large Language Models
