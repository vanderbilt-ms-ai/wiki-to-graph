---
kind: fact
---

# Compute-Optimal Scaling

## Summary
The principle that under a fixed compute budget a transformer language model's parameter count and number of training tokens should be scaled **equally** — for every doubling of model size, double the training data.

## Explanation
Earlier scaling practice (embodied by [[GPT-3]]) grew parameters while holding data roughly constant, producing large but **undertrained** models. By training 400+ models from 70M to 16B parameters across 5–500B tokens, [[Hoffmann 2022]] derived a compute-optimal frontier and confirmed it with [[Chinchilla]]: a 70B compute-optimal model beats a 280B model and even the 175B [[GPT-3]]. This refines — and partly corrects — the notion of [[Scale and Scaling]], shifting it from *parameters-first* to *parameters-and-data-balanced*, and has direct consequences for [[Emergent Capabilities]] (they depend on training tokens, not just size).

## Related
- [[Chinchilla]] — the model that confirmed the principle
- [[Scale and Scaling]] — the broader idea this principle refines
- [[GPT-3]] — the parameters-first recipe it corrects
- [[Emergent Capabilities]] — which depend on training tokens as well as size
- [[Foundation Models]] — the models whose training budgets it governs

## Contradictions / tensions
- [[GPT-3]] — adding parameters without proportionally more data is compute-inefficient and leaves capability on the table.

## Sources
- raw/06_chinchilla.md — Training Compute-Optimal Large Language Models
