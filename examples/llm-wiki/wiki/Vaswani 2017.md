---
type: source
medium: paper
locator: raw/01_attention_is_all_you_need.md
author: Vaswani, Shazeer, Parmar, Uszkoreit, Jones, Gomez, Kaiser, Polosukhin
date: 2017
topics: Language models / Architecture
---

# Attention Is All You Need

## Summary
Proposes the Transformer, a sequence transduction model built entirely on attention with no recurrence or convolution, which trains faster and translates better than the recurrent and convolutional models it replaced.

## Explanation
The model reaches 28.4 BLEU on WMT 2014 English-to-German, more than 2 BLEU over the previous best including ensembles, and a single-model state of the art of 41.8 BLEU on English-to-French after 3.5 days on eight GPUs.

The paper introduces the components every later model in this collection inherits: scaled dot-product attention, multi-head attention, sinusoidal positional encodings, and residual connections with layer normalization around each sub-layer of an encoder-decoder stack.

## Related
- [[Transformer]] — the architecture this paper introduces
- [[Scaled Dot-Product Attention]] — the attention function it defines
- [[Multi-Head Attention]] — how it runs attention in parallel subspaces
- [[Positional Encoding]] — how it supplies word order without recurrence
- [[Encoder-Decoder Architecture]] — the two-stack structure it uses
- [[Layer Normalization]] — the normalization wrapped around every sub-layer
