---
kind: schema
---

# BERT

## Summary
BERT (Bidirectional Encoder Representations from Transformers, 2018) is an **encoder-only** [[Transformer]] pre-trained to produce deeply bidirectional language representations, then fine-tuned for downstream tasks. It set new state-of-the-art on eleven NLP tasks.

## Explanation
BERT uses the [[Encoder-Decoder Architecture]]'s encoder half only, so every layer conditions on both left and right context via bidirectional [[Self-Attention]]. It is pre-trained with two objectives — [[Masked Language Modeling]] (predict masked tokens) and [[Next Sentence Prediction]] — then adapted through [[Pre-training and Fine-tuning]] with a single added output layer per task. Sizes: BASE (110M params) and LARGE (340M). BERT is a canonical early example of a [[Foundation Models]].

## Related
[[Transformer]] · [[Encoder-Decoder Architecture]] · [[Self-Attention]] · [[Masked Language Modeling]] · [[Next Sentence Prediction]] · [[Pre-training and Fine-tuning]] · [[Foundation Models]] · [[GPT-3]]

## Contradictions / tensions
- **Directionality vs [[GPT-3]]:** BERT argues bidirectional context is essential for understanding and uses [[Masked Language Modeling]] to achieve it. [[GPT-3]] is unidirectional (left-to-right) yet reaches strong performance through scale — a genuine tension in how "language understanding" is best learned.
- **Adaptation method:** BERT relies on [[Pre-training and Fine-tuning]] (gradient updates per task); [[GPT-3]] argues fine-tuning is often unnecessary given [[In-Context Learning]].

## Sources
- raw/02_bert.md (Devlin et al., 2018)
