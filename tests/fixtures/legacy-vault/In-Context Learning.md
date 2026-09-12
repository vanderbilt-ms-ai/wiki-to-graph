---
kind: concept
---

# In-Context Learning

## Summary
The ability, highlighted by [[GPT-3]], to perform a new task by conditioning on instructions and/or a few examples provided in the prompt at inference time — with **no gradient updates or fine-tuning**.

## Explanation
In-context learning covers zero-shot (instruction only), one-shot, and few-shot (a handful of demonstrations) settings. The task is specified purely via text interaction. This reframes adaptation: instead of [[Pre-training and Fine-tuning]] with labeled data per task, the same frozen model handles many tasks from the prompt. It is closely tied to [[Few-Shot Learning]] and is an [[Emergent Capabilities|emergent capability]] of [[Scale and Scaling]].

## Related
[[GPT-3]] · [[Few-Shot Learning]] · [[Emergent Capabilities]] · [[Scale and Scaling]] · [[Pre-training and Fine-tuning]]

## Contradictions / tensions
Stands in contrast to [[BERT]]'s fine-tuning-based adaptation. [[RLHF]] later shows that some kinds of fine-tuning (on human feedback) still add substantial value beyond prompting — so "no fine-tuning needed" is not the whole story.

## Sources
- raw/03_gpt3.md (Brown et al., 2020)
