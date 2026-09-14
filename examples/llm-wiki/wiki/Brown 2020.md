---
type: source
medium: paper
locator: raw/03_gpt3.md
author: Brown, Mann, Ryder, Subbiah, Kaplan, et al.
date: 2020
topics: Language models / Scaling
---

# Language Models are Few-Shot Learners

## Summary
Trains GPT-3, a 175-billion-parameter autoregressive language model, and shows that scale makes it competitive on many tasks from a few demonstrations in the prompt, with no gradient updates.

## Explanation
GPT-3 is ten times larger than any previous dense language model. It is evaluated in zero-, one- and few-shot settings, where few-shot performance improves markedly with size and sometimes approaches fine-tuned state of the art.

The paper documents on-the-fly reasoning, three-digit arithmetic and word unscrambling from the prompt alone, and also names datasets where few-shot learning still struggles.

## Related
- [[GPT-3]] — the model this paper introduces
- [[In-Context Learning]] — the adaptation mode it demonstrates
- [[Few-Shot Learning]] — the evaluation setting it centres on
- [[Emergent Capabilities]] — the behaviours it reports appearing with scale
- [[Scale and Scaling]] — the lever it argues drives capability

## Contradictions / tensions
- [[Ouyang 2022]] — GPT-3 treats scale as the route to capability; InstructGPT shows a 1.3B aligned model preferred over the 175B GPT-3.
- [[Hoffmann 2022]] — GPT-3 grows parameters with roughly fixed data; the compute-optimal analysis finds it significantly undertrained.
