---
kind: schema
---

# Positional Encoding

## Summary
Because the [[Transformer]] has no recurrence or convolution, it must inject information about token order explicitly. Positional encodings — added to the input embeddings — provide this.

## Explanation
The original Transformer uses fixed sinusoidal functions of different frequencies: `PE(pos,2i)=sin(pos/10000^(2i/dmodel))` and `PE(pos,2i+1)=cos(...)`. These have the same dimension as the embeddings so the two can be summed. The sinusoidal choice was hypothesized to help the model attend by relative positions and to extrapolate to sequence lengths longer than seen in training. The authors found learned positional embeddings performed nearly identically. Without positional encoding, [[Self-Attention]] would be order-invariant.

## Related
[[Transformer]] · [[Self-Attention]]

## Contradictions / tensions
Minor: sinusoidal vs learned positional embeddings gave nearly identical results; the authors chose sinusoidal for possible length extrapolation, not accuracy.

## Sources
- raw/01_attention_is_all_you_need.md (Vaswani et al., 2017)
