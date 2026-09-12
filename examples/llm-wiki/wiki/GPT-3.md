---
kind: schema
---

# GPT-3

## Summary
GPT-3 is a 175-billion-parameter **decoder-only** [[Autoregressive Language Model]]. Its central claim: scaling up language models yields strong task-agnostic [[Few-Shot Learning]] via [[In-Context Learning]], often without any fine-tuning.

## Explanation
Introduced in [[Brown 2020]], GPT-3 keeps only the decoder half of the [[Encoder-Decoder Architecture]], using masked [[Self-Attention]]. At 10x the size of any prior dense LM, it exhibits [[Emergent Capabilities]] — on-the-fly reasoning, arithmetic, word unscrambling — specified purely through the prompt. This shifts the paradigm from [[Pre-training and Fine-tuning]] toward pretrain-then-prompt. GPT-3 is a headline example of [[Foundation Models]], and its scale-centric framing is directly challenged by [[RLHF]].

## Related
- [[Autoregressive Language Model]] — the modeling style it uses
- [[In-Context Learning]] — how it adapts to tasks
- [[Few-Shot Learning]] — the setting its results centre on
- [[Scale and Scaling]] — the lever it argues drives capability
- [[Emergent Capabilities]] — the behaviours it reports at 175B
- [[Transformer]] — the architecture it is built on
- [[Encoder-Decoder Architecture]] — it keeps only the decoder
- [[Self-Attention]] — used in masked form
- [[Foundation Models]] — a headline example of the paradigm
- [[RLHF]] — the method that aligns it into InstructGPT
- [[BERT]] — the encoder-only model it is contrasted with
- [[Pre-training and Fine-tuning]] — the recipe it moves away from
- [[Chinchilla]] — the smaller model that outperforms it
- [[Compute-Optimal Scaling]] — the principle its training budget violates

## Contradictions / tensions
- [[BERT]] — GPT-3 is unidirectional and forgoes masked language modeling and per-task fine-tuning, contradicting BERT's premise that both are needed for strong understanding.
- [[RLHF]] — GPT-3 implies bigger is better, but a 1.3B aligned InstructGPT is preferred by humans over the 175B GPT-3.
- [[Chinchilla]] — at 175B parameters GPT-3 had far too little training data for its size; a 70B compute-optimal model beats it.

## Sources
- raw/03_gpt3.md — Language Models are Few-Shot Learners
