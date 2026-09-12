---
kind: procedure
---

# Proximal Policy Optimization

## Summary
PPO is the reinforcement-learning algorithm used in the RL stage of [[RLHF]] to fine-tune the language model policy against the learned reward signal from [[Reward Modeling]].

## Explanation
In [[RLHF]], the pre-trained/supervised model is treated as a policy that generates outputs; [[Reward Modeling]] provides the reward. PPO updates the policy to maximize this reward while a constraint (a KL penalty toward the supervised model) keeps it from drifting too far and exploiting the reward model. This produces InstructGPT — a model better aligned to user intent than the base [[GPT-3]].

## Related
[[RLHF]] · [[Reward Modeling]] · [[Alignment]] · [[GPT-3]]

## Contradictions / tensions
None across the current sources.

## Sources
- raw/05_rlhf_instructgpt.md (Ouyang et al., 2022)
