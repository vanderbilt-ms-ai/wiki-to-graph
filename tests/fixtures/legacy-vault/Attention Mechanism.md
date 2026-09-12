---
kind: concept
---

# Attention Mechanism

## Summary
An attention mechanism maps a query and a set of key–value pairs to an output computed as a weighted sum of the values, where each weight reflects the compatibility of the query with the corresponding key. It lets a model focus on relevant parts of the input regardless of distance.

## Explanation
Before the [[Transformer]], attention was typically bolted onto recurrent networks. *Attention Is All You Need* showed attention alone is sufficient. The specific form used is [[Scaled Dot-Product Attention]], run in parallel across multiple heads via [[Multi-Head Attention]]. When queries, keys, and values all come from the same sequence, it is called [[Self-Attention]].

Attention is what allows the [[Transformer]] to model long-range dependencies with short path lengths between any two positions, and underlies both [[BERT]] and [[GPT-3]].

## Related
[[Transformer]] · [[Scaled Dot-Product Attention]] · [[Multi-Head Attention]] · [[Self-Attention]]

## Contradictions / tensions
None across the current sources.

## Sources
- raw/01_attention_is_all_you_need.md (Vaswani et al., 2017)
