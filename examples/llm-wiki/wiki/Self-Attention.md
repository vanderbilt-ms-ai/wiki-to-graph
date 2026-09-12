---
kind: schema
---

# Self-Attention

## Summary
Self-attention (intra-attention) is an [[Attention Mechanism]] where the queries, keys, and values all come from the same sequence, letting each position attend to every other position to build a context-aware representation.

## Explanation
Self-attention is the core computation of the [[Transformer]] in [[Vaswani 2017]]. A self-attention layer connects all positions with O(1) sequential operations and a constant maximum path length, versus O(n) for recurrent layers — this is why Transformers parallelize well and capture long-range dependencies. In the decoder, self-attention is *masked* so a position can only attend to earlier positions, preserving the [[Autoregressive Language Model]] property used by [[GPT-3]]. [[BERT]] instead uses unmasked (bidirectional) self-attention. In practice it is realized as [[Multi-Head Attention]] over [[Scaled Dot-Product Attention]].

## Related
- [[Attention Mechanism]] — the general idea it specializes
- [[Multi-Head Attention]] — how it is run in practice
- [[Scaled Dot-Product Attention]] — the function each head computes
- [[Transformer]] — the architecture it is the core of
- [[BERT]] — uses it unmasked in both directions
- [[Autoregressive Language Model]] — uses it masked, left to right

## Contradictions / tensions
None across the current sources; bidirectional versus masked use is a design choice, not a disagreement.

## Sources
- raw/01_attention_is_all_you_need.md — Attention Is All You Need
