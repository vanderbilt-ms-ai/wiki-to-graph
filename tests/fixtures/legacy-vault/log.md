# Compilation Log

## 2026-07-23 — Initial compilation
- **Sources ingested (5):** Attention Is All You Need (2017), BERT (2018), GPT-3 (2020), Foundation Models (2021), RLHF/InstructGPT (2022).
- **Entity pages created (24):** Transformer, Attention Mechanism, Scaled Dot-Product Attention, Multi-Head Attention, Self-Attention, Positional Encoding, Encoder-Decoder Architecture, Layer Normalization, BERT, Masked Language Modeling, Next Sentence Prediction, Pre-training and Fine-tuning, GPT-3, Autoregressive Language Model, In-Context Learning, Few-Shot Learning, Scale and Scaling, Emergent Capabilities, Foundation Models, Homogenization, RLHF, Reward Modeling, Proximal Policy Optimization, Alignment.
- **Navigational pages:** index.md, log.md.
- **Contradictions flagged:** BERT bidirectional vs GPT-3 unidirectional; fine-tuning vs in-context learning; scale-first (GPT-3) vs alignment-first (RLHF); emergence as capability vs risk.

## 2026-07-23 — Compounding pass (Step 5): added Chinchilla
- **Source added:** Training Compute-Optimal Large Language Models (Chinchilla, Hoffmann et al., 2022) → raw/06_chinchilla.md.
- **New entity pages (2):** Chinchilla, Compute-Optimal Scaling.
- **Existing pages enriched (4):** Scale and Scaling, GPT-3, Emergent Capabilities, index.
- **New contradiction flagged:** GPT-3 (parameters-first scaling) was *undertrained*; Chinchilla's 70B compute-optimal model beats the 175B GPT-3. This is a second, independent challenge to "bigger is better" (the first being RLHF's alignment result).
- **Compounding observed:** the "Scale and Scaling" page went from one outgoing tension (vs RLHF) to two (vs RLHF and vs Chinchilla), and gained 2 new outgoing links — the graph densified around the scaling cluster rather than just adding isolated nodes.

## 2026-07-23 — Linting/audit pass (Step 6)
Audited all 28 pages for the four issues the pattern calls out:
1. **Orphan pages** (no incoming links): **NONE.** Every entity page is linked from at least one other page.
2. **Missing pages** (concepts referenced in `[[brackets]]` with no page yet): **NONE.** All link targets resolve.
3. **Contradictions:** all cross-paper tensions are explicitly flagged on the relevant pages (not silently resolved) — directionality (BERT vs GPT-3), adaptation (fine-tuning vs in-context learning), scale-vs-alignment (GPT-3 vs RLHF), scale-vs-data-balance (GPT-3 vs Chinchilla), emergence as capability vs risk.
4. **Stale claims:** GPT-3's parameters-first scaling claim is superseded by [[Compute-Optimal Scaling]]. Per the pattern, this is **flagged as a contradiction on the GPT-3 page rather than deleted** — the wiki preserves the historical claim and its later correction side by side.

Lightly-connected pages to watch as the wiki grows: Positional Encoding (in=2), Layer Normalization, Next Sentence Prediction, Reward Modeling. All above the orphan threshold; no action needed yet.

No fixes required — the wiki is internally consistent.

## How to extend this wiki
1. Drop a new source into `../raw/` (PDF, .md, or .txt).
2. Run the compilation prompt:
   > A new source has been added. Read it alongside the existing wiki pages. Update any existing entity pages affected by this new source. Create new entity pages for any new concepts introduced. Flag any contradictions with previously compiled knowledge.
3. Every ~20 new pages, run the linting prompt to catch orphan pages, missing pages, contradictions, and stale claims.

## Note on sources
The `raw/` folder currently holds markdown source files (abstracts + key points) because arXiv was not directly reachable from the build sandbox. Run `../download_papers.sh` on a networked machine to fetch the original PDFs alongside them.
