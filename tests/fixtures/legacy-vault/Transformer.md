---
kind: schema
---

# Transformer

## Summary
The Transformer is a neural network architecture based entirely on [[Attention Mechanism]], dispensing with recurrence and convolution. Introduced in *Attention Is All You Need* (2017), it became the foundation for essentially all modern large language models.

## Explanation
The Transformer uses an [[Encoder-Decoder Architecture]] where each stack is built from repeated layers of [[Self-Attention]] and position-wise feed-forward networks, wrapped with residual connections and [[Layer Normalization]]. Because [[Self-Attention]] relates all positions in a sequence in a constant number of sequential operations, the Transformer is far more parallelizable than recurrent networks and better at learning long-range dependencies. Word order is supplied by [[Positional Encoding]] rather than recurrence. Its attention is computed via [[Scaled Dot-Product Attention]] and run in parallel across several [[Multi-Head Attention]] heads.

Later architectures specialize the two halves: [[BERT]] keeps only the encoder for bidirectional understanding, while [[GPT-3]] keeps only the decoder as an [[Autoregressive Language Model]]. These are the building blocks of [[Foundation Models]].

## Related
[[Attention Mechanism]] · [[Self-Attention]] · [[Multi-Head Attention]] · [[Scaled Dot-Product Attention]] · [[Positional Encoding]] · [[Encoder-Decoder Architecture]] · [[Layer Normalization]] · [[BERT]] · [[GPT-3]]

## Contradictions / tensions
None internal. Note the architectural fork downstream: [[BERT]] uses the encoder only (bidirectional), [[GPT-3]] uses the decoder only (unidirectional) — see those pages.

## Sources
- raw/01_attention_is_all_you_need.md (Vaswani et al., 2017)
