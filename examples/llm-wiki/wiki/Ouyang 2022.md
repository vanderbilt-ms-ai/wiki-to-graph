---
type: source
medium: paper
locator: raw/05_rlhf_instructgpt.md
author: Ouyang, Wu, Jiang, Almeida, et al.
date: 2022
---

# Training Language Models to Follow Instructions with Human Feedback

## Summary
Aligns GPT-3 to user intent with reinforcement learning from human feedback, producing InstructGPT, whose 1.3B-parameter version is preferred by human evaluators over the 175B GPT-3.

## Explanation
The method has three stages: supervised fine-tuning on labeler demonstrations, training a reward model on labeler rankings of outputs, and optimizing the policy against that reward with PPO.

InstructGPT also improves truthfulness and reduces toxic output generation, with minimal performance regressions on public NLP datasets.

## Related
- [[RLHF]] — the technique this paper introduces
- [[Reward Modeling]] — the second stage of its pipeline
- [[Proximal Policy Optimization]] — the optimizer in its third stage
- [[Alignment]] — the goal the method pursues
