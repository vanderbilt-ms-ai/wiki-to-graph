---
kind: concept
---

# Few-Shot Learning

## Summary
Performing a task from only a few examples. In the [[GPT-3]] context, few-shot means providing a handful of demonstrations in the prompt via [[In-Context Learning]], rather than training on a large labeled dataset.

## Explanation
[[GPT-3]] evaluates zero-, one-, and few-shot settings and shows that few-shot performance improves markedly with model [[Scale and Scaling]], sometimes approaching fine-tuned state-of-the-art. This contrasts with the prior norm of task-specific datasets of thousands of examples used in [[Pre-training and Fine-tuning]]. Few-shot ability is one of the [[Emergent Capabilities]] associated with large [[Foundation Models]].

## Related
[[GPT-3]] · [[In-Context Learning]] · [[Scale and Scaling]] · [[Emergent Capabilities]] · [[Pre-training and Fine-tuning]] · [[Foundation Models]]

## Contradictions / tensions
[[GPT-3]] itself notes datasets where few-shot learning still struggles, tempering strong claims. Its usefulness also depends on [[Alignment]], per [[RLHF]].

## Sources
- raw/03_gpt3.md (Brown et al., 2020)
