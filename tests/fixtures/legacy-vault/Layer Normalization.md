---
kind: schema
---

# Layer Normalization

## Summary
A normalization technique applied around each sub-layer in the [[Transformer]], combined with residual connections: the output of each sub-layer is `LayerNorm(x + Sublayer(x))`.

## Explanation
Residual connections plus layer normalization stabilize and speed up training of deep stacks, letting the [[Transformer]] scale to many layers. All sub-layers and embedding layers produce outputs of dimension dmodel=512 to make the residual sums well-defined. This pattern is inherited by [[BERT]], [[GPT-3]], and other [[Foundation Models]].

## Related
[[Transformer]] · [[Encoder-Decoder Architecture]]

## Contradictions / tensions
None across the current sources. (Placement of the norm — pre- vs post-layer — varies in later work but is outside the current sources.)

## Sources
- raw/01_attention_is_all_you_need.md (Vaswani et al., 2017)
