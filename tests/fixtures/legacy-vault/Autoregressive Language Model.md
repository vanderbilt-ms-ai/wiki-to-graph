---
kind: concept
---

# Autoregressive Language Model

## Summary
A language model that generates a sequence one token at a time, each token conditioned only on the previously generated (left-context) tokens. This is the modeling style of [[GPT-3]] and the decoder side of the [[Transformer]].

## Explanation
Autoregression is enforced in the [[Transformer]] decoder by *masked* [[Self-Attention]]: position i can attend only to positions ≤ i, so predictions for i depend only on known earlier outputs. [[GPT-3]] is a pure decoder-only autoregressive model. This left-to-right objective differs from [[BERT]]'s bidirectional [[Masked Language Modeling]]. Autoregressive generation is what makes these models natural text generators and underlies [[In-Context Learning]].

## Related
[[GPT-3]] · [[Transformer]] · [[Self-Attention]] · [[Masked Language Modeling]] · [[BERT]] · [[In-Context Learning]]

## Contradictions / tensions
The autoregressive (unidirectional) objective contrasts with [[BERT]]'s bidirectional [[Masked Language Modeling]] — a core difference in how the two families learn.

## Sources
- raw/01_attention_is_all_you_need.md (Vaswani et al., 2017); raw/03_gpt3.md (Brown et al., 2020)
