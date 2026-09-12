---
kind: procedure
---

# Pre-training and Fine-tuning

## Summary
A two-stage transfer-learning recipe: first pre-train a model on large unlabeled text with a self-supervised objective, then fine-tune it (with gradient updates) on a smaller labeled dataset for a specific task.

## Explanation
[[BERT]] is the canonical example: pre-train with [[Masked Language Modeling]] + [[Next Sentence Prediction]], then add one output layer and fine-tune per task. This paradigm made strong NLP results widely accessible and is a defining mechanism of [[Foundation Models]] (train once, adapt many times). [[GPT-3]] challenges the *fine-tuning* half of this recipe by showing that [[In-Context Learning]] can solve tasks with no gradient updates. [[RLHF]] is a specialized fine-tuning stage layered on top of a pre-trained model.

## Related
[[BERT]] · [[Masked Language Modeling]] · [[Next Sentence Prediction]] · [[Foundation Models]] · [[In-Context Learning]] · [[GPT-3]] · [[RLHF]]

## Contradictions / tensions
- [[GPT-3]] argues task-specific fine-tuning is often unnecessary (use [[In-Context Learning]] instead), whereas [[BERT]] treats fine-tuning as the standard adaptation path.
- [[RLHF]] shows that a *particular* kind of fine-tuning (on human feedback) can matter more than scale — see [[Alignment]].

## Sources
- raw/02_bert.md (Devlin et al., 2018); raw/03_gpt3.md (Brown et al., 2020)
