---
kind: procedure
---

# Next Sentence Prediction

## Summary
A secondary pre-training objective in [[BERT]]: given two sentences A and B, predict whether B actually follows A in the corpus. Intended to teach inter-sentence relationships useful for tasks like question answering and natural language inference.

## Explanation
Next Sentence Prediction (NSP) complements [[Masked Language Modeling]] during [[Pre-training and Fine-tuning]]. Sentence pairs are joined with special [CLS]/[SEP] tokens, and the [CLS] representation is used for the binary prediction. NSP was later questioned by follow-up work (e.g., RoBERTa) as providing limited benefit, but within the current sources it is presented as a core part of BERT's recipe.

## Related
[[BERT]] · [[Masked Language Modeling]] · [[Pre-training and Fine-tuning]]

## Contradictions / tensions
Within the current sources none; noted as an area later research revisited (outside current sources).

## Sources
- raw/02_bert.md (Devlin et al., 2018)
