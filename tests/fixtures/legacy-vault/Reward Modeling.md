---
kind: procedure
---

# Reward Modeling

## Summary
The step in [[RLHF]] where a model is trained to predict human preferences: given multiple model outputs for a prompt, it learns to score them consistent with human rankings, providing the reward signal for RL.

## Explanation
Human labelers rank several candidate outputs for each prompt; these rankings train a reward model to approximate "what humans prefer." That learned reward then guides policy optimization via [[Proximal Policy Optimization]]. Reward modeling is what lets [[Alignment]] scale beyond the limited set of hand-written demonstrations used in the supervised stage — humans need only *compare* outputs, not write ideal ones.

## Related
[[RLHF]] · [[Proximal Policy Optimization]] · [[Alignment]]

## Contradictions / tensions
None internal. A known limitation (within the paper's framing): the policy can overoptimize against an imperfect reward model, so [[Proximal Policy Optimization]] is constrained to stay near the supervised model.

## Sources
- raw/05_rlhf_instructgpt.md (Ouyang et al., 2022)
