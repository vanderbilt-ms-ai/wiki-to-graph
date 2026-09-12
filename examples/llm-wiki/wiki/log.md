# Compilation Log

## 2026-07-23 — Initial compilation
- **Sources ingested (5):** Attention Is All You Need (2017), BERT (2018), GPT-3 (2020), Foundation Models (2021), RLHF/InstructGPT (2022).
- **Entity pages created (24):** Transformer, Attention Mechanism, Scaled Dot-Product Attention, Multi-Head Attention, Self-Attention, Positional Encoding, Encoder-Decoder Architecture, Layer Normalization, BERT, Masked Language Modeling, Next Sentence Prediction, Pre-training and Fine-tuning, GPT-3, Autoregressive Language Model, In-Context Learning, Few-Shot Learning, Scale and Scaling, Emergent Capabilities, Foundation Models, Homogenization, RLHF, Reward Modeling, Proximal Policy Optimization, Alignment.
- **Navigational pages:** index.md, log.md.

## 2026-07-23 — Compounding pass: added Chinchilla
- **Source added:** Training Compute-Optimal Large Language Models (Chinchilla, Hoffmann et al., 2022), raw/06_chinchilla.md
- **New entity pages (2):** Chinchilla, Compute-Optimal Scaling.
- **Existing pages enriched (4):** Scale and Scaling, GPT-3, Emergent Capabilities, index.
- **New contradiction flagged:** GPT-3's parameters-first scaling left it undertrained; Chinchilla's 70B compute-optimal model beats the 175B GPT-3.

## 2026-09-12 — Page-contract pass
- **Source pages added (6):** one per paper, so each artifact is a node of its own and every concept cites it.
- **Related links** each carry a one-line reason, so the graph records why two pages are connected and not only that they are.
- **Contradictions** rewritten as one bullet per disagreement, led by the page actually in tension; "None" entries no longer link anything.
- **Sources** listed one citation per line.

## How to extend this wiki
1. Drop a new source into `../raw/` (PDF, .md, or .txt) and give it a source page.
2. Update any existing entity pages the new source affects; create pages for new concepts.
3. Record each new disagreement on the pages that actually disagree.
4. Rebuild the graph: `python3 skills/wiki-to-graph/scripts/wiki_to_graph.py build examples/llm-wiki/wiki -o build/graph.json`.
