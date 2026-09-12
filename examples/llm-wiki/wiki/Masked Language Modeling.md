---
kind: procedure
---

# Masked Language Modeling

## Summary
A pre-training objective: randomly mask ~15% of input tokens and train the model to predict them from surrounding context on both sides.

## Explanation
Introduced by [[Devlin 2018]] for [[BERT]], masked language modeling (MLM) is what enables deep bidirectionality. Standard left-to-right language modeling (as in [[GPT-3]]'s [[Autoregressive Language Model]]) cannot condition on future tokens without trivially "seeing the answer." By masking tokens and predicting them, MLM lets every layer's [[Self-Attention]] use both left and right context. It is paired with [[Next Sentence Prediction]] during [[Pre-training and Fine-tuning]].

## Related
- [[BERT]] — the model it was designed for
- [[Self-Attention]] — masking lets it use both directions safely
- [[Next Sentence Prediction]] — the objective it is paired with
- [[Pre-training and Fine-tuning]] — the first stage it belongs to
- [[Autoregressive Language Model]] — the left-to-right objective it is contrasted with

## Contradictions / tensions
- [[Autoregressive Language Model]] — bidirectional, non-generative pre-training optimizes a different target from left-to-right generation, even though both are called language modeling.

## Sources
- raw/02_bert.md — BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding
