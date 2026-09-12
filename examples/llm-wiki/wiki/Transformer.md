---
kind: schema
---

# Transformer

## Summary
The Transformer is a neural network architecture based entirely on attention, dispensing with recurrence and convolution. It became the foundation for essentially all modern large language models.

## Explanation
Introduced in [[Vaswani 2017]], the Transformer uses an [[Encoder-Decoder Architecture]] where each stack is built from repeated layers of [[Self-Attention]] and position-wise feed-forward networks, wrapped with residual connections and [[Layer Normalization]]. Because [[Self-Attention]] relates all positions in a sequence in a constant number of sequential operations, the Transformer is far more parallelizable than recurrent networks and better at learning long-range dependencies. Word order is supplied by [[Positional Encoding]] rather than recurrence. Its [[Attention Mechanism]] is computed via [[Scaled Dot-Product Attention]] and run in parallel across several [[Multi-Head Attention]] heads.

Later architectures specialize the two halves: [[BERT]] keeps only the encoder for bidirectional understanding, while [[GPT-3]] keeps only the decoder as an [[Autoregressive Language Model]]. These are the building blocks of [[Foundation Models]].

## Related
- [[Attention Mechanism]] — the only mechanism it is built on
- [[Self-Attention]] — its core computation
- [[Multi-Head Attention]] — how it runs attention in parallel
- [[Scaled Dot-Product Attention]] — the attention function it uses
- [[Positional Encoding]] — how it gets word order without recurrence
- [[Encoder-Decoder Architecture]] — its two-stack structure
- [[Layer Normalization]] — what stabilizes its deep stacks
- [[BERT]] — keeps only its encoder
- [[GPT-3]] — keeps only its decoder

## Contradictions / tensions
None across the current sources.

## Sources
- raw/01_attention_is_all_you_need.md — Attention Is All You Need
