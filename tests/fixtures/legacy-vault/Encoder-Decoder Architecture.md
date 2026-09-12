---
kind: schema
---

# Encoder-Decoder Architecture

## Summary
The structure the [[Transformer]] follows: an encoder maps an input sequence to continuous representations, and a decoder generates an output sequence one element at a time, consuming previously generated symbols ([[Autoregressive Language Model]] behavior).

## Explanation
In the Transformer, the encoder is a stack of N=6 identical layers (self-attention + feed-forward), and the decoder adds a third sub-layer that attends over the encoder output ("encoder–decoder attention"). Both use residual connections and [[Layer Normalization]]. Later models specialize this design: [[BERT]] uses **encoder-only** (good for understanding tasks via [[Masked Language Modeling]]), while [[GPT-3]] uses **decoder-only** (good for generation as an [[Autoregressive Language Model]]).

## Related
[[Transformer]] · [[Self-Attention]] · [[Layer Normalization]] · [[BERT]] · [[GPT-3]] · [[Autoregressive Language Model]]

## Contradictions / tensions
None internal. The encoder-only vs decoder-only split is a design divergence, not a contradiction — see [[BERT]] and [[GPT-3]].

## Sources
- raw/01_attention_is_all_you_need.md (Vaswani et al., 2017)
