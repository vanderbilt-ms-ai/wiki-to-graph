---
kind: schema
---

# Scaled Dot-Product Attention

## Summary
The specific [[Attention Mechanism]] used in the [[Transformer]]: `Attention(Q, K, V) = softmax(QKᵀ / √dₖ) V`. Dot products of queries and keys are scaled by 1/√dₖ before the softmax.

## Explanation
The scaling factor 1/√dₖ is the key detail. For large key dimension dₖ, unscaled dot products grow large in magnitude, pushing the softmax into regions with vanishingly small gradients. Dividing by √dₖ keeps the softmax in a well-behaved range. Dot-product attention is preferred over additive attention because it can be implemented with highly optimized matrix multiplication, making it fast and memory-efficient. Multiple instances run in parallel form [[Multi-Head Attention]]; when Q, K, V share a source it becomes [[Self-Attention]].

## Related
[[Attention Mechanism]] · [[Multi-Head Attention]] · [[Self-Attention]] · [[Transformer]]

## Contradictions / tensions
None across the current sources.

## Sources
- raw/01_attention_is_all_you_need.md (Vaswani et al., 2017)
