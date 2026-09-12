---
type: source
medium: paper
locator: raw/06_chinchilla.md
author: Hoffmann, Borgeaud, Mensch, et al.
date: 2022
---

# Training Compute-Optimal Large Language Models

## Summary
Finds that large language models are significantly undertrained, and that for compute-optimal training parameters and training tokens should be scaled equally.

## Explanation
The analysis trains over 400 models from 70M to over 16B parameters on 5 to 500 billion tokens. The resulting 70B-parameter Chinchilla uses the same compute as the 280B Gopher with four times more data.

Chinchilla uniformly outperforms Gopher, GPT-3, Jurassic-1 and Megatron-Turing NLG, and reaches 67.5% average accuracy on MMLU, more than 7 points above Gopher.

## Related
- [[Chinchilla]] — the model this paper trains
- [[Compute-Optimal Scaling]] — the principle it establishes
