---
kind: schema
---

# Multi-Head Attention

## Summary
Instead of a single attention function, the [[Transformer]] linearly projects queries, keys, and values h times into lower-dimensional subspaces, applies [[Scaled Dot-Product Attention]] in parallel on each, then concatenates and projects the results.

## Explanation
Multiple heads let the model jointly attend to information from different representation subspaces at different positions — something a single averaged attention head inhibits. [[Vaswani 2017]] uses h=8 heads with dₖ=dᵥ=dmodel/h=64, so total computation is similar to single-head attention at full dimensionality. This is the mechanism that gives [[Self-Attention]] its expressive power and is inherited by [[BERT]] and [[GPT-3]].

## Related
- [[Scaled Dot-Product Attention]] — the function each head runs
- [[Self-Attention]] — gains its expressive power from multiple heads
- [[Attention Mechanism]] — the general idea it parallelizes
- [[Transformer]] — the architecture that introduced it

## Contradictions / tensions
None across the current sources.

## Sources
- raw/01_attention_is_all_you_need.md — Attention Is All You Need
