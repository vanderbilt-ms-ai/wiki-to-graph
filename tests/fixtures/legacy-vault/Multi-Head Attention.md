---
kind: schema
---

# Multi-Head Attention

## Summary
Instead of a single attention function, the [[Transformer]] linearly projects queries, keys, and values h times into lower-dimensional subspaces, applies [[Scaled Dot-Product Attention]] in parallel on each, then concatenates and projects the results.

## Explanation
Multiple heads let the model jointly attend to information from different representation subspaces at different positions — something a single averaged attention head inhibits. The original Transformer uses h=8 heads with dₖ=dᵥ=dmodel/h=64, so total computation is similar to single-head attention at full dimensionality. This is the mechanism that gives [[Self-Attention]] its expressive power and is inherited by [[BERT]] and [[GPT-3]].

## Related
[[Scaled Dot-Product Attention]] · [[Self-Attention]] · [[Attention Mechanism]] · [[Transformer]]

## Contradictions / tensions
None across the current sources.

## Sources
- raw/01_attention_is_all_you_need.md (Vaswani et al., 2017)
