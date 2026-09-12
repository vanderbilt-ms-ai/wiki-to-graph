---
kind: procedure
---

# Proximal Policy Optimization

## Summary
PPO is the reinforcement-learning algorithm used in the RL stage of [[RLHF]] to fine-tune the language model policy against the learned reward signal from [[Reward Modeling]].

## Explanation
In the pipeline of [[Ouyang 2022]], the pre-trained and supervised model is treated as a policy that generates outputs; [[Reward Modeling]] provides the reward. PPO updates the policy to maximize this reward while a constraint (a KL penalty toward the supervised model) keeps it from drifting too far and exploiting the reward model. This produces InstructGPT — a model better aligned to user intent than the base [[GPT-3]].

## Related
- [[RLHF]] — the pipeline whose final stage it performs
- [[Reward Modeling]] — the source of the reward it maximizes
- [[Alignment]] — the goal the optimization serves
- [[GPT-3]] — the base model the policy starts from

## Contradictions / tensions
None across the current sources.

## Sources
- raw/05_rlhf_instructgpt.md — Training Language Models to Follow Instructions with Human Feedback
