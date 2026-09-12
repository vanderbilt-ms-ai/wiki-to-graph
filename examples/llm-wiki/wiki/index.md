# Wiki Index

A compounding knowledge base compiled from six foundational AI papers (see `../raw/`). Each entry is a single-concept entity page linked with `[[wiki-links]]`, and each paper has its own source page. Open this folder as a vault in Obsidian and press Ctrl/Cmd+G for the graph view.

## Sources
- [[Vaswani 2017]] — Attention Is All You Need
- [[Devlin 2018]] — BERT: bidirectional pre-training
- [[Brown 2020]] — GPT-3: language models are few-shot learners
- [[Bommasani 2021]] — foundation models: opportunities and risks
- [[Ouyang 2022]] — InstructGPT: alignment from human feedback
- [[Hoffmann 2022]] — Chinchilla: compute-optimal training

## Transformer architecture
- [[Transformer]] — attention-only architecture underpinning modern LLMs
- [[Attention Mechanism]] — query/key/value weighted lookup
- [[Scaled Dot-Product Attention]] — the softmax(QKᵀ/√dₖ)V core
- [[Multi-Head Attention]] — parallel attention over subspaces
- [[Self-Attention]] — sequence attending to itself
- [[Positional Encoding]] — injecting token order
- [[Encoder-Decoder Architecture]] — the two-stack design
- [[Layer Normalization]] — residual + norm for deep stacks

## Understanding and pre-training
- [[BERT]] — bidirectional encoder-only model
- [[Masked Language Modeling]] — BERT's core objective
- [[Next Sentence Prediction]] — BERT's secondary objective
- [[Pre-training and Fine-tuning]] — the transfer-learning recipe

## Scale and few-shot learning
- [[GPT-3]] — 175B decoder-only model
- [[Autoregressive Language Model]] — left-to-right generation
- [[In-Context Learning]] — learning from the prompt
- [[Few-Shot Learning]] — tasks from a few examples
- [[Scale and Scaling]] — capability from size
- [[Emergent Capabilities]] — abilities that appear with scale

## Compute-optimal scaling
- [[Chinchilla]] — 70B model that beats 175B GPT-3
- [[Compute-Optimal Scaling]] — scale params and data equally

## The paradigm
- [[Foundation Models]] — broad, adaptable models
- [[Homogenization]] — one model, many applications

## Alignment
- [[RLHF]] — reinforcement learning from human feedback
- [[Reward Modeling]] — learning human preferences
- [[Proximal Policy Optimization]] — the RL optimizer
- [[Alignment]] — helpful, honest, harmless

## Key cross-paper tensions
- [[BERT]] — bidirectional understanding versus GPT-3's unidirectional generation
- [[In-Context Learning]] — prompting versus per-task fine-tuning
- [[RLHF]] — a 1.3B aligned model versus GPT-3's bigger-is-better
- [[Chinchilla]] — balanced parameters and data versus GPT-3's parameters-first scaling
- [[Emergent Capabilities]] — capability for GPT-3, risk for the foundation-models report
