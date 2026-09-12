# Wiki Index

A compounding knowledge base compiled from 5 foundational AI papers (see `../raw/`). Each entry is a single-concept entity page linked with `[[wiki-links]]`. Open this folder as a vault in Obsidian and press Ctrl/Cmd+G for the graph view.

## Transformer architecture (Vaswani et al., 2017)
- [[Transformer]] — attention-only architecture underpinning modern LLMs
- [[Attention Mechanism]] — query/key/value weighted lookup
- [[Scaled Dot-Product Attention]] — the softmax(QKᵀ/√dₖ)V core
- [[Multi-Head Attention]] — parallel attention over subspaces
- [[Self-Attention]] — sequence attending to itself
- [[Positional Encoding]] — injecting token order
- [[Encoder-Decoder Architecture]] — the two-stack design
- [[Layer Normalization]] — residual + norm for deep stacks

## Understanding & pretraining (Devlin et al., 2018)
- [[BERT]] — bidirectional encoder-only model
- [[Masked Language Modeling]] — BERT's core objective
- [[Next Sentence Prediction]] — BERT's secondary objective
- [[Pre-training and Fine-tuning]] — the transfer-learning recipe

## Scale & few-shot learning (Brown et al., 2020)
- [[GPT-3]] — 175B decoder-only model
- [[Autoregressive Language Model]] — left-to-right generation
- [[In-Context Learning]] — learning from the prompt
- [[Few-Shot Learning]] — tasks from a few examples
- [[Scale and Scaling]] — capability from size
- [[Emergent Capabilities]] — abilities that appear with scale

## Compute-optimal scaling (Hoffmann et al., 2022)
- [[Chinchilla]] — 70B model that beats 175B GPT-3
- [[Compute-Optimal Scaling]] — scale params and data equally

## The paradigm (Bommasani et al., 2021)
- [[Foundation Models]] — broad, adaptable models
- [[Homogenization]] — one model, many applications

## Alignment (Ouyang et al., 2022)
- [[RLHF]] — reinforcement learning from human feedback
- [[Reward Modeling]] — learning human preferences
- [[Proximal Policy Optimization]] — the RL optimizer
- [[Alignment]] — helpful, honest, harmless

## Key cross-paper tensions (flagged during compilation)
- **Directionality:** [[BERT]] (bidirectional, [[Masked Language Modeling]]) vs [[GPT-3]] (unidirectional [[Autoregressive Language Model]]).
- **Adaptation:** [[Pre-training and Fine-tuning]] vs [[In-Context Learning]].
- **Scale vs alignment:** [[GPT-3]]'s "bigger is better" vs [[RLHF]] (1.3B aligned model beats 175B).
- **Scale vs data balance:** [[GPT-3]]'s parameters-first scaling vs [[Chinchilla]] / [[Compute-Optimal Scaling]] (GPT-3 was undertrained; a 70B model beats it).
- **Emergence:** capability ([[GPT-3]]) vs risk ([[Foundation Models]]), and dependent on compute-optimal scale, not raw size ([[Chinchilla]]).
