---
kind: concept
---

# In-Context Learning

## Summary
The ability to perform a new task by conditioning on instructions and/or a few examples provided in the prompt at inference time — with **no gradient updates or fine-tuning**.

## Explanation
Highlighted by [[Brown 2020]] for [[GPT-3]], in-context learning covers zero-shot (instruction only), one-shot, and few-shot (a handful of demonstrations) settings. The task is specified purely via text interaction. This reframes adaptation: instead of [[Pre-training and Fine-tuning]] with labeled data per task, the same frozen model handles many tasks from the prompt. It is closely tied to [[Few-Shot Learning]] and is an [[Emergent Capabilities|emergent capability]] of [[Scale and Scaling]].

## Related
- [[GPT-3]] — the model that demonstrated it at scale
- [[Few-Shot Learning]] — its most studied setting
- [[Emergent Capabilities]] — it appears only in large models
- [[Scale and Scaling]] — what makes it work
- [[Pre-training and Fine-tuning]] — the gradient-based adaptation it replaces

## Contradictions / tensions
- [[Pre-training and Fine-tuning]] — adapting from the prompt removes the per-task gradient updates that BERT's recipe depends on.
- [[RLHF]] — fine-tuning on human feedback still adds value that prompting cannot, so no fine-tuning needed is not the whole story.

## Sources
- raw/03_gpt3.md — Language Models are Few-Shot Learners
