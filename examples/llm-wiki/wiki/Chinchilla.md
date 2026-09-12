---
kind: schema
---

# Chinchilla

## Summary
Chinchilla is a 70B-parameter model trained on 4× more data than Gopher under the same compute budget. It outperforms much larger models — including the 175B [[GPT-3]] — establishing that most large LMs were **undertrained**.

## Explanation
Chinchilla, trained in [[Hoffmann 2022]], is the empirical proof of [[Compute-Optimal Scaling]]: by training 400+ models, the authors show that for a fixed compute budget, parameters and training tokens should scale **equally**. Applying this, a smaller-but-better-fed model beats parameter-heavy giants (Gopher 280B, [[GPT-3]] 175B, Megatron-Turing 530B) and reaches 67.5% on MMLU. It also costs less to fine-tune ([[Pre-training and Fine-tuning]]) and to serve. Chinchilla directly reshapes what [[Scale and Scaling]] means.

## Related
- [[Compute-Optimal Scaling]] — the principle it was trained to demonstrate
- [[Scale and Scaling]] — the idea its result reshapes
- [[GPT-3]] — the larger model it outperforms
- [[Pre-training and Fine-tuning]] — being smaller makes it cheaper to adapt
- [[Foundation Models]] — the class of large pre-trained model it belongs to
- [[Transformer]] — the architecture it is built on

## Contradictions / tensions
- [[GPT-3]] — a 70B model trained on far more data beats the 175B GPT-3, showing GPT-3 was significantly undertrained.
- [[Scale and Scaling]] — raw parameter count is the wrong axis; data must grow with model size.

## Sources
- raw/06_chinchilla.md — Training Compute-Optimal Large Language Models
