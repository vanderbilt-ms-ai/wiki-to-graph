---
kind: concept
---

# Autoregressive Language Model

## Summary
A language model that generates a sequence one token at a time, each token conditioned only on the previously generated (left-context) tokens. This is the modeling style of [[GPT-3]] and the decoder side of the [[Transformer]].

## Explanation
Autoregression is enforced in the [[Transformer]] decoder of [[Vaswani 2017]] by *masked* [[Self-Attention]]: position i can attend only to positions ≤ i, so predictions for i depend only on known earlier outputs. [[Brown 2020]] scales this into [[GPT-3]], a pure decoder-only autoregressive model. This left-to-right objective differs from [[BERT]]'s bidirectional [[Masked Language Modeling]]. Autoregressive generation is what makes these models natural text generators and underlies [[In-Context Learning]].

## Related
- [[GPT-3]] — the headline autoregressive model in the sources
- [[Transformer]] — whose decoder enforces the left-to-right constraint
- [[Self-Attention]] — masked so each position sees only earlier ones
- [[Masked Language Modeling]] — the bidirectional objective it is contrasted with
- [[BERT]] — the bidirectional model on the other side of that contrast
- [[In-Context Learning]] — the prompting ability generation makes possible

## Contradictions / tensions
- [[Masked Language Modeling]] — predicting the next token from left context only is a different objective from predicting masked tokens from both sides; both are called language modeling but optimize different things.

## Sources
- raw/01_attention_is_all_you_need.md — Attention Is All You Need
- raw/03_gpt3.md — Language Models are Few-Shot Learners
