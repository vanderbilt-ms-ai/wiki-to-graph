---
kind: concept
---

# Foundation Models

## Summary
A model trained on broad data at scale and adaptable to a wide range of downstream tasks. Examples given include [[BERT]], DALL-E, and [[GPT-3]].

## Explanation
The term was coined by Stanford's CRFM in [[Bommasani 2021]]. The report names two defining properties: **emergence** ([[Emergent Capabilities]] arise from [[Scale and Scaling]]) and **[[Homogenization]]** (one model underlies many applications). Foundation models are built on standard deep learning, the [[Transformer]], and [[Pre-training and Fine-tuning]], but their scale changes their character. The report is explicitly sociotechnical, spanning capabilities, technical principles, applications (law, healthcare, education), and societal impact (inequity, misuse, environment). [[RLHF]] is one concrete technique for improving how such models serve users ([[Alignment]]).

## Related
- [[BERT]] — an example the report gives
- [[GPT-3]] — another example the report gives
- [[Transformer]] — the architecture these models are built on
- [[Pre-training and Fine-tuning]] — the train-once, adapt-many recipe behind them
- [[Emergent Capabilities]] — one of the two defining properties
- [[Homogenization]] — the other defining property
- [[Scale and Scaling]] — what gives these models their character
- [[RLHF]] — a technique for making such a model serve users
- [[Alignment]] — the goal that technique pursues

## Contradictions / tensions
- [[GPT-3]] — the report is deliberately non-committal about net benefit and stresses systemic risk, against GPT-3's capability-first framing.

## Sources
- raw/04_foundation_models.md — On the Opportunities and Risks of Foundation Models
