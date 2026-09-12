---
kind: schema
---

# Chinchilla

## Summary
Chinchilla (*Training Compute-Optimal Large Language Models*, DeepMind, 2022) is a 70B-parameter model trained on 4× more data than Gopher under the same compute budget. It outperforms much larger models — including the 175B [[GPT-3]] — establishing that most large LMs were **undertrained**.

## Explanation
Chinchilla is the empirical proof of [[Compute-Optimal Scaling]]: by training 400+ models, the authors show that for a fixed compute budget, parameters and training tokens should scale **equally**. Applying this, a smaller-but-better-fed model beats parameter-heavy giants (Gopher 280B, [[GPT-3]] 175B, Megatron-Turing 530B) and reaches 67.5% on MMLU. It also costs less to fine-tune ([[Pre-training and Fine-tuning]]) and to serve. Chinchilla directly reshapes what [[Scale and Scaling]] means.

## Related
[[Compute-Optimal Scaling]] · [[Scale and Scaling]] · [[GPT-3]] · [[Pre-training and Fine-tuning]] · [[Foundation Models]] · [[Transformer]]

## Contradictions / tensions
- **vs [[GPT-3]] and the "bigger is better" reading of [[Scale and Scaling]]:** Chinchilla shows GPT-3 (175B) was significantly undertrained; a 70B model with more data beats it. Raw parameter count is the wrong axis — data matters as much as size.
- Complements [[RLHF]]'s critique from a different angle: RLHF says *alignment* can beat scale; Chinchilla says *better-balanced training* can beat scale. Both undercut parameters-first thinking.

## Sources
- raw/06_chinchilla.md (Hoffmann et al., 2022)
