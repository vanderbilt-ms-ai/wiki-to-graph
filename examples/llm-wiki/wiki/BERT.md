---
kind: schema
---

# BERT

## Summary
BERT (Bidirectional Encoder Representations from Transformers) is an **encoder-only** [[Transformer]] pre-trained to produce deeply bidirectional language representations, then fine-tuned for downstream tasks. It set new state-of-the-art on eleven NLP tasks.

## Explanation
Introduced in [[Devlin 2018]], BERT uses the [[Encoder-Decoder Architecture]]'s encoder half only, so every layer conditions on both left and right context via bidirectional [[Self-Attention]]. It is pre-trained with two objectives — [[Masked Language Modeling]] (predict masked tokens) and [[Next Sentence Prediction]] — then adapted through [[Pre-training and Fine-tuning]] with a single added output layer per task. Sizes: BASE (110M params) and LARGE (340M). BERT is a canonical early example of the [[Foundation Models]] paradigm.

## Related
- [[Transformer]] — the architecture it specializes
- [[Encoder-Decoder Architecture]] — it keeps only the encoder half
- [[Self-Attention]] — used unmasked so every layer sees both directions
- [[Masked Language Modeling]] — its primary pre-training objective
- [[Next Sentence Prediction]] — its secondary pre-training objective
- [[Pre-training and Fine-tuning]] — the adaptation recipe it made standard
- [[Foundation Models]] — a canonical early example of the paradigm
- [[GPT-3]] — the decoder-only model it is most often contrasted with

## Contradictions / tensions
- [[GPT-3]] — BERT argues bidirectional context is essential for understanding; GPT-3 is left-to-right yet reaches strong performance through scale.
- [[In-Context Learning]] — BERT adapts through per-task gradient updates; GPT-3 argues fine-tuning is often unnecessary when tasks are specified in the prompt.

## Sources
- raw/02_bert.md — BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding
