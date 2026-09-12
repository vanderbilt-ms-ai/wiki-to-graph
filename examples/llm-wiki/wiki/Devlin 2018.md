---
type: source
medium: paper
locator: raw/02_bert.md
author: Devlin, Chang, Lee, Toutanova
date: 2018
---

# BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding

## Summary
Introduces BERT, an encoder-only Transformer pre-trained to condition on both left and right context in every layer, then fine-tuned with one added output layer per task.

## Explanation
BERT set a new state of the art on eleven NLP tasks, including a GLUE score of 80.5% (7.7 points absolute), MultiNLI accuracy of 86.7%, and SQuAD v1.1 test F1 of 93.2.

It is pre-trained with two objectives, masked language modeling and next sentence prediction, in BASE (110M) and LARGE (340M) sizes, and argues that deep bidirectionality is what strong language understanding requires.

## Related
- [[BERT]] — the model this paper introduces
- [[Masked Language Modeling]] — its primary pre-training objective
- [[Next Sentence Prediction]] — its secondary pre-training objective
- [[Pre-training and Fine-tuning]] — the adaptation recipe it made standard

## Contradictions / tensions
- [[Brown 2020]] — BERT argues bidirectional context plus per-task fine-tuning is needed for strong understanding; GPT-3 reaches strong results left-to-right and without fine-tuning.
