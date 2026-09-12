---
kind: concept
---

# Self-Attention

## Summary
Self-attention (intra-attention) is an [[Attention Mechanism]] where the queries, keys, and values all come from the same sequence, letting each position attend to every other position to build a context-aware representation.

## Explanation
Self-attention is the core computation of the [[Transformer]]. A self-attention layer connects all positions with O(1) sequential operations and a constant maximum path length, versus O(n) for recurrent layers — this is why Transformers parallelize well and capture long-range dependencies. In the decoder, self-attention is *masked* so a position can only attend to earlier positions, preserving the [[Autoregressive Language Model]] property used by [[GPT-3]]. [[BERT]] instead uses unmasked (bidirectional) self-attention. In practice it is realized as [[Multi-Head Attention]] over [[Scaled Dot-Product Attention]].

## Related
[[Attention Mechanism]] · [[Multi-Head Attention]] · [[Scaled Dot-Product Attention]] · [[Transformer]] · [[BERT]] · [[Autoregressive Language Model]]

## Contradictions / tensions
Directional use differs: [[BERT]] uses bidirectional self-attention; [[GPT-3]] uses masked (left-to-right) self-attention. See [[Masked Language Modeling]].

## Sources
- raw/01_attention_is_all_you_need.md (Vaswani et al., 2017)
