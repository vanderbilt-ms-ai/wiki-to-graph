---
kind: fact
---

# Compute-Optimal Scaling

## Summary
The principle, established by [[Chinchilla]] (Hoffmann et al., 2022), that under a fixed compute budget a transformer language model's parameter count and number of training tokens should be scaled **equally** — for every doubling of model size, double the training data.

## Explanation
Earlier scaling practice (embodied by [[GPT-3]]) grew parameters while holding data roughly constant, producing large but **undertrained** models. By training 400+ models from 70M to 16B parameters across 5–500B tokens, [[Chinchilla]] derived a compute-optimal frontier and confirmed it: a 70B compute-optimal model beats a 280B and even the 175B [[GPT-3]]. This refines — and partly corrects — the notion of [[Scale and Scaling]], shifting it from *parameters-first* to *parameters-and-data-balanced*, and has direct consequences for [[Emergent Capabilities]] (they depend on training tokens, not just size).

## Related
[[Chinchilla]] · [[Scale and Scaling]] · [[GPT-3]] · [[Emergent Capabilities]] · [[Foundation Models]]

## Contradictions / tensions
Contradicts the parameters-first framing implicit in [[GPT-3]]: adding parameters without proportionally adding data is compute-inefficient and leaves capability on the table.

## Sources
- raw/06_chinchilla.md (Hoffmann et al., 2022)
