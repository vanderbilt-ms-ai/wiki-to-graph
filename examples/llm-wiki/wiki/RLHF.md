---
kind: procedure
---

# RLHF

## Summary
Reinforcement Learning from Human Feedback: the technique used to align [[GPT-3]] into **InstructGPT**. It fine-tunes a model to follow user intent using human preference data.

## Explanation
[[Ouyang 2022]] describes RLHF as a three-step pipeline layered on a pre-trained model:
1. **Supervised fine-tuning (SFT)** on labeler-written demonstrations.
2. **[[Reward Modeling]]** — train a reward model to predict human rankings of outputs.
3. **RL optimization** — fine-tune the policy against the reward model using [[Proximal Policy Optimization]].

The goal is [[Alignment]]: making models helpful, honest, and harmless. It is a specialized form of [[Pre-training and Fine-tuning]] and the bridge from raw [[Foundation Models]] to modern assistants.

## Related
- [[Reward Modeling]] — its second stage
- [[Proximal Policy Optimization]] — the optimizer in its third stage
- [[Alignment]] — the goal it pursues
- [[GPT-3]] — the base model it aligns into InstructGPT
- [[Pre-training and Fine-tuning]] — it is a specialized fine-tuning stage
- [[Foundation Models]] — it adapts such models into assistants
- [[Scale and Scaling]] — the lever its result is weighed against

## Contradictions / tensions
- [[GPT-3]] — the 1.3B InstructGPT is preferred by humans over the 175B GPT-3, a direct rebuttal of the scale-first framing.
- [[In-Context Learning]] — where GPT-3 argues fine-tuning is often unnecessary, targeted fine-tuning on human feedback yields large gains in usefulness, truthfulness, and reduced toxicity.

## Sources
- raw/05_rlhf_instructgpt.md — Training Language Models to Follow Instructions with Human Feedback
