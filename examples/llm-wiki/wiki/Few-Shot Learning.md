---
kind: concept
---

# Few-Shot Learning

## Summary
Performing a task from only a few examples. In the [[GPT-3]] context, few-shot means providing a handful of demonstrations in the prompt via [[In-Context Learning]], rather than training on a large labeled dataset.

## Explanation
[[Brown 2020]] evaluates zero-, one-, and few-shot settings for [[GPT-3]] and shows that few-shot performance improves markedly with model [[Scale and Scaling]], sometimes approaching fine-tuned state-of-the-art. This contrasts with the prior norm of task-specific datasets of thousands of examples used in [[Pre-training and Fine-tuning]]. Few-shot ability is one of the [[Emergent Capabilities]] associated with large [[Foundation Models]]. The same paper also names datasets where few-shot learning still struggles.

## Related
- [[GPT-3]] — the model whose few-shot results define the setting
- [[In-Context Learning]] — the mechanism few-shot prompting relies on
- [[Scale and Scaling]] — few-shot performance improves with size
- [[Emergent Capabilities]] — few-shot ability appears as models grow
- [[Pre-training and Fine-tuning]] — the data-hungry alternative it replaces
- [[Foundation Models]] — the paradigm in which it is a headline ability

## Contradictions / tensions
- [[RLHF]] — few-shot ability does not by itself make a model follow intent; fine-tuning on human feedback is what made outputs preferred.

## Sources
- raw/03_gpt3.md — Language Models are Few-Shot Learners
