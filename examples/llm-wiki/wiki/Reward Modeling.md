---
kind: procedure
---

# Reward Modeling

## Summary
The step in [[RLHF]] where a model is trained to predict human preferences: given multiple model outputs for a prompt, it learns to score them consistent with human rankings, providing the reward signal for RL.

## Explanation
In [[Ouyang 2022]], human labelers rank several candidate outputs for each prompt; these rankings train a reward model to approximate "what humans prefer." That learned reward then guides policy optimization via [[Proximal Policy Optimization]]. Reward modeling is what lets [[Alignment]] scale beyond the limited set of hand-written demonstrations used in the supervised stage — humans need only *compare* outputs, not write ideal ones. Because the policy can overoptimize against an imperfect reward model, the optimization is constrained to stay near the supervised model.

## Related
- [[RLHF]] — the pipeline it is the second stage of
- [[Proximal Policy Optimization]] — the optimizer that consumes its reward
- [[Alignment]] — which it lets scale beyond demonstrations

## Contradictions / tensions
None across the current sources.

## Sources
- raw/05_rlhf_instructgpt.md — Training Language Models to Follow Instructions with Human Feedback
