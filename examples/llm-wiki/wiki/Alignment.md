---
kind: concept
---

# Alignment

## Summary
Making a model's behavior match user intent and human values — in the current sources, making language models **helpful, honest, and harmless** rather than merely fluent or large.

## Explanation
[[Ouyang 2022]], the paper behind [[RLHF]], frames the problem sharply: making models bigger does not inherently make them better at following intent; large models can be untruthful, toxic, or unhelpful — i.e. *unaligned*. Alignment is pursued by fine-tuning on human feedback via [[Reward Modeling]] and [[Proximal Policy Optimization]]. The payoff: InstructGPT (1.3B) is preferred over [[GPT-3]] (175B). Because of [[Homogenization]], aligning a base model among the [[Foundation Models]] benefits every downstream application built on it.

## Related
- [[RLHF]] — the technique the current sources use to pursue it
- [[Reward Modeling]] — how human preferences become a training signal
- [[Proximal Policy Optimization]] — the optimizer that pushes the model toward those preferences
- [[GPT-3]] — the unaligned base model InstructGPT improves on
- [[Foundation Models]] — the kind of model whose alignment propagates downstream
- [[Homogenization]] — why aligning one base model matters so widely
- [[Scale and Scaling]] — the lever alignment is weighed against

## Contradictions / tensions
- [[Scale and Scaling]] — a 1.3B aligned model is preferred over the 175B GPT-3, so parameter count alone does not buy usefulness.

## Sources
- raw/05_rlhf_instructgpt.md — Training Language Models to Follow Instructions with Human Feedback
