---
kind: procedure
---

# Masked Language Modeling

## Summary
The pre-training objective introduced by [[BERT]]: randomly mask ~15% of input tokens and train the model to predict them from surrounding context on both sides.

## Explanation
Masked Language Modeling (MLM) is what enables [[BERT]]'s deep bidirectionality. Standard left-to-right language modeling (as in [[GPT-3]]'s [[Autoregressive Language Model]]) cannot condition on future tokens without trivially "seeing the answer." By masking tokens and predicting them, MLM lets every layer's [[Self-Attention]] use both left and right context. It is paired with [[Next Sentence Prediction]] during [[Pre-training and Fine-tuning]].

## Related
[[BERT]] · [[Self-Attention]] · [[Next Sentence Prediction]] · [[Pre-training and Fine-tuning]] · [[Autoregressive Language Model]]

## Contradictions / tensions
MLM (bidirectional, non-generative pretraining) contrasts with the [[Autoregressive Language Model]] objective of [[GPT-3]] (left-to-right, generative). Both are "language modeling" but optimize different things.

## Sources
- raw/02_bert.md (Devlin et al., 2018)
