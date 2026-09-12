---
kind: concept
---

# Emergent Capabilities

## Summary
Abilities that appear in large models but are absent (or much weaker) in smaller ones, arising implicitly from [[Scale and Scaling]] rather than being explicitly trained.

## Explanation
[[Brown 2020]] documents emergent behaviors in [[GPT-3]] such as on-the-fly reasoning, 3-digit arithmetic, word unscrambling, and using novel words in a sentence — all via [[In-Context Learning]]. [[Bommasani 2021]] elevates *emergence* to one of the two defining properties of [[Foundation Models]] (alongside [[Homogenization]]), noting that because these capabilities are emergent, we often lack a clear understanding of how the models work, when they fail, or what they can do.

## Related
- [[GPT-3]] — the model in which the sources document emergent behaviour
- [[Scale and Scaling]] — the lever emergence is attributed to
- [[In-Context Learning]] — the setting where the behaviours show up
- [[Few-Shot Learning]] — an ability that strengthens with size
- [[Foundation Models]] — for which emergence is a defining property
- [[Homogenization]] — the other defining property of the paradigm
- [[Compute-Optimal Scaling]] — which ties capability to data as well as size
- [[Chinchilla]] — evidence that capability tracks training tokens

## Contradictions / tensions
- [[Foundation Models]] — GPT-3 presents emergence as capability, while the foundation-models report presents the same unpredictability as a risk.
- [[Compute-Optimal Scaling]] — capability depends on training tokens as much as parameters, so emergence tracks compute-optimal scale rather than raw size.

## Sources
- raw/03_gpt3.md — Language Models are Few-Shot Learners
- raw/04_foundation_models.md — On the Opportunities and Risks of Foundation Models
