---
kind: schema
---

# Encoder-Decoder Architecture

## Summary
The structure the [[Transformer]] follows: an encoder maps an input sequence to continuous representations, and a decoder generates an output sequence one element at a time, consuming previously generated symbols ([[Autoregressive Language Model]] behavior).

## Explanation
In the Transformer of [[Vaswani 2017]], the encoder is a stack of N=6 identical layers (self-attention + feed-forward), and the decoder adds a third sub-layer that attends over the encoder output ("encoder–decoder attention"). Both use residual connections and [[Layer Normalization]]. Later models specialize this design: [[BERT]] uses **encoder-only** (good for understanding tasks via [[Masked Language Modeling]]), while [[GPT-3]] uses **decoder-only** (good for generation as an [[Autoregressive Language Model]]).

## Related
- [[Transformer]] — the model that uses this structure
- [[Self-Attention]] — the main computation inside both stacks
- [[Layer Normalization]] — wrapped around every sub-layer in both stacks
- [[BERT]] — keeps only the encoder
- [[GPT-3]] — keeps only the decoder
- [[Autoregressive Language Model]] — the behaviour of the decoder side

## Contradictions / tensions
None across the current sources.

## Sources
- raw/01_attention_is_all_you_need.md — Attention Is All You Need
