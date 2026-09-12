---
kind: procedure
---

# RLHF

## Summary
Reinforcement Learning from Human Feedback: the technique in *Training Language Models to Follow Instructions with Human Feedback* (2022) used to align [[GPT-3]] into **InstructGPT**. It fine-tunes a model to follow user intent using human preference data.

## Explanation
RLHF is a three-step pipeline layered on a pre-trained model:
1. **Supervised fine-tuning (SFT)** on labeler-written demonstrations.
2. **[[Reward Modeling]]** — train a reward model to predict human rankings of outputs.
3. **RL optimization** — fine-tune the policy against the reward model using [[Proximal Policy Optimization]].

The goal is [[Alignment]]: making models helpful, honest, and harmless. It is a specialized form of [[Pre-training and Fine-tuning]] and the bridge from raw [[Foundation Models]] to modern assistants like ChatGPT.

## Related
[[Reward Modeling]] · [[Proximal Policy Optimization]] · [[Alignment]] · [[GPT-3]] · [[Pre-training and Fine-tuning]] · [[Foundation Models]] · [[Scale and Scaling]]

## Contradictions / tensions
- **Directly rebuts [[GPT-3]]'s scale-first framing:** the 1.3B InstructGPT is preferred by humans over the 175B [[GPT-3]] — a 100x smaller model, better aligned, wins on human preference.
- **Reframes [[In-Context Learning]]:** where [[GPT-3]] argues fine-tuning is often unnecessary, RLHF shows targeted fine-tuning on human feedback yields large gains in usefulness, truthfulness, and reduced toxicity.

## Sources
- raw/05_rlhf_instructgpt.md (Ouyang et al., 2022)
