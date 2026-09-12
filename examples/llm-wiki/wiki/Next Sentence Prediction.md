---
kind: procedure
---

# Next Sentence Prediction

## Summary
A secondary pre-training objective: given two sentences A and B, predict whether B actually follows A in the corpus. Intended to teach inter-sentence relationships useful for tasks like question answering and natural language inference.

## Explanation
Next Sentence Prediction (NSP) is part of [[BERT]]'s recipe in [[Devlin 2018]], complementing [[Masked Language Modeling]] during [[Pre-training and Fine-tuning]]. Sentence pairs are joined with special [CLS]/[SEP] tokens, and the [CLS] representation is used for the binary prediction. NSP was later questioned by follow-up work as providing limited benefit, but within the current sources it is presented as a core part of BERT's recipe.

## Related
- [[BERT]] — the model it trains
- [[Masked Language Modeling]] — the primary objective it accompanies
- [[Pre-training and Fine-tuning]] — the pre-training stage it belongs to

## Contradictions / tensions
None across the current sources.

## Sources
- raw/02_bert.md — BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding
