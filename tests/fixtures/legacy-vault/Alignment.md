---
kind: concept
---

# Alignment

## Summary
Making a model's behavior match user intent and human values — in the current sources, making language models **helpful, honest, and harmless** rather than merely fluent or large.

## Explanation
[[RLHF]] frames the problem sharply: making models bigger does not inherently make them better at following intent; large models can be untruthful, toxic, or unhelpful — i.e. *unaligned*. Alignment is pursued by fine-tuning on human feedback via [[Reward Modeling]] and [[Proximal Policy Optimization]]. The payoff: InstructGPT (1.3B) is preferred over [[GPT-3]] (175B). Because of [[Homogenization]], aligning a base [[Foundation Models]] benefits every downstream application built on it.

## Related
[[RLHF]] · [[Reward Modeling]] · [[Proximal Policy Optimization]] · [[GPT-3]] · [[Foundation Models]] · [[Homogenization]] · [[Scale and Scaling]]

## Contradictions / tensions
Alignment reframes the value of [[Scale and Scaling]]: it shows a small aligned model can beat a much larger unaligned one, countering the "bigger is better" reading of [[GPT-3]].

## Sources
- raw/05_rlhf_instructgpt.md (Ouyang et al., 2022)
