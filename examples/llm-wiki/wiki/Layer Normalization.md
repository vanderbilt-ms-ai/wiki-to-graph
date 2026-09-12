---
kind: schema
---

# Layer Normalization

## Summary
A normalization technique applied around each sub-layer in the [[Transformer]], combined with residual connections: the output of each sub-layer is `LayerNorm(x + Sublayer(x))`.

## Explanation
In [[Vaswani 2017]], residual connections plus layer normalization stabilize and speed up training of deep stacks, letting the [[Transformer]] scale to many layers. All sub-layers and embedding layers produce outputs of dimension dmodel=512 to make the residual sums well-defined. This pattern is inherited by [[BERT]], [[GPT-3]], and other [[Foundation Models]].

## Related
- [[Transformer]] — the architecture that wraps every sub-layer in it
- [[Encoder-Decoder Architecture]] — used in both the encoder and decoder stacks

## Contradictions / tensions
None across the current sources.

## Sources
- raw/01_attention_is_all_you_need.md — Attention Is All You Need
