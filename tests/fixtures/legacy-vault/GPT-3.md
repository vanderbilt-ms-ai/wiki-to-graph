---
kind: schema
---

# GPT-3

## Summary
GPT-3 (*Language Models are Few-Shot Learners*, 2020) is a 175-billion-parameter **decoder-only** [[Autoregressive Language Model]]. Its central claim: scaling up language models yields strong task-agnostic [[Few-Shot Learning]] via [[In-Context Learning]], often without any fine-tuning.

## Explanation
GPT-3 keeps only the decoder half of the [[Encoder-Decoder Architecture]], using masked [[Self-Attention]]. At 10x the size of any prior dense LM, it exhibits [[Emergent Capabilities]] — on-the-fly reasoning, arithmetic, word unscrambling — specified purely through the prompt. This shifts the paradigm from [[Pre-training and Fine-tuning]] toward pretrain-then-prompt. GPT-3 is a headline [[Foundation Models]], and its scale-centric framing is directly challenged by [[RLHF]].

## Related
[[Autoregressive Language Model]] · [[In-Context Learning]] · [[Few-Shot Learning]] · [[Scale and Scaling]] · [[Emergent Capabilities]] · [[Transformer]] · [[Encoder-Decoder Architecture]] · [[Self-Attention]] · [[Foundation Models]] · [[RLHF]] · [[BERT]] · [[Pre-training and Fine-tuning]] · [[Chinchilla]] · [[Compute-Optimal Scaling]]

## Contradictions / tensions
- **vs [[BERT]]:** GPT-3 is unidirectional and forgoes [[Masked Language Modeling]] and per-task fine-tuning, contradicting BERT's premise that bidirectionality + fine-tuning are needed for strong understanding.
- **vs [[RLHF]]:** GPT-3 implies "bigger is better." [[RLHF]] shows a 1.3B aligned model (InstructGPT) is preferred by humans over the 175B GPT-3 — scale alone does not guarantee usefulness or [[Alignment]].
- **vs [[Chinchilla]]:** [[Compute-Optimal Scaling]] shows GPT-3 was **significantly undertrained** — at 175B parameters it had far too little training data for its size. A 70B compute-optimal model (Chinchilla) beats it. GPT-3's parameters-first scaling was compute-inefficient.

## Sources
- raw/03_gpt3.md (Brown et al., 2020)
