---
kind: procedure
---

# Pre-training and Fine-tuning

## Summary
A two-stage transfer-learning recipe: first pre-train a model on large unlabeled text with a self-supervised objective, then fine-tune it (with gradient updates) on a smaller labeled dataset for a specific task.

## Explanation
[[Devlin 2018]] makes [[BERT]] the canonical example: pre-train with [[Masked Language Modeling]] + [[Next Sentence Prediction]], then add one output layer and fine-tune per task. This paradigm made strong NLP results widely accessible and is a defining mechanism of [[Foundation Models]] (train once, adapt many times). [[Brown 2020]] challenges the *fine-tuning* half of this recipe with [[GPT-3]], showing that [[In-Context Learning]] can solve tasks with no gradient updates. [[RLHF]] is a specialized fine-tuning stage layered on top of a pre-trained model.

## Related
- [[BERT]] — the canonical example of the recipe
- [[Masked Language Modeling]] — the self-supervised objective of its first stage
- [[Next Sentence Prediction]] — a second objective in that stage
- [[Foundation Models]] — for which train once, adapt many is defining
- [[In-Context Learning]] — the prompt-based alternative to its second stage
- [[GPT-3]] — the model that questions the need to fine-tune
- [[RLHF]] — a specialized fine-tuning stage built on it

## Contradictions / tensions
- [[In-Context Learning]] — GPT-3 argues task-specific fine-tuning is often unnecessary, whereas BERT treats fine-tuning as the standard adaptation path.
- [[Scale and Scaling]] — fine-tuning on human feedback can matter more than adding parameters.

## Sources
- raw/02_bert.md — BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding
- raw/03_gpt3.md — Language Models are Few-Shot Learners
