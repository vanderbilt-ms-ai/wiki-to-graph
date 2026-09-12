# LLM Wiki → Knowledge Space: Ontology & Graph Spec

**Version 0.1** · Status: draft · Applies to: any LLM-wiki folder of markdown entity pages
using the standard section scaffolding.

## 1. Purpose

An LLM wiki is *already* a graph: entity pages are nodes and `[[wiki-links]]` are edges. But
in the raw markdown that graph is only implicit — you can read it, you can't run PageRank on
it. This spec defines a small, explicit ontology and a deterministic mapping from the wiki's
markdown to a typed property graph that graph algorithms (traversal, centrality, community
detection, cycle checks) can operate on directly.

The key idea: **the section a link appears in determines the edge type.** Because every entity
page uses the same sections, the parse is deterministic.

## 2. Source scaffolding (the input contract)

Each entity page is a markdown file whose filename stem is its title. Every page contains the
same second-level sections:

```
# <Title>
## Summary            — 1–3 sentence definition
## Explanation        — prose body, may contain [[links]]
## Related            — a line of [[links]] to associated concepts
## Contradictions / tensions   — [[links]] to concepts this one conflicts with
## Sources            — bullet list of source documents / citations
```

Navigational files (`index.md`, `log.md`) do **not** follow this shape, but they are **not
discarded** — they are kept as hub nodes (§3.1) because they carry real structure (the index
groups every concept; the log records provenance and which contradictions were flagged). Only
`README`-style files are excluded by default. The parser degrades gracefully: a missing section
just yields no edges of that type; an unknown extra section in a concept page is treated as body
text (→ `mentions`).

## 3. Ontology

### 3.1 Node types

| Type | One per… | Key properties |
|------|----------|----------------|
| `concept` | entity page | `id` (slug of title), `kind`, `title`, `summary`, `explanation`, `sources[]`, `file`, `in_degree`, `out_degree`, `edges[]` |
| `source`  | an ingested artifact — authored as a page with `type: source`, or generated from a `## Sources` bullet | `id` (slug), `locator`, `medium`, `title`, plus `summary`/`explanation`/`file` when authored, `ref` when generated, `edges[]` |
| `index`   | the `index.md` hub (0–1) | `id`, `title`, `file`, `edges[]` |
| `log`     | the `log.md` provenance file (0–1) | `id`, `title`, `file`, `edges[]` |

`id` is a kebab-case slug of the title, lowercased. It is stable and unique — the primary key.

Two orthogonal classifiers on a node:

- **`type`** — structural role: `concept | source | index | log`. Set per page via
  frontmatter `type:`; falls back to the filename stem (`index.md`, `log.md`), else `concept`.
- **`kind`** — the knowledge taxonomy of a **concept** node: **`concept | fact | schema | procedure`**
  (default `concept`; set per page via frontmatter `kind:`). `source/index/log` have `kind: null`.

These axes are independent and must not be conflated. `kind` classifies *knowledge*; an
artifact is not knowledge. **A paper is not a `fact` — it CONTAINS facts.** It is a
`source` whose claims become `fact` atoms that `cites` it. The same holds for a web page,
a book, a deck, a transcript or a repository: the artifact is the source, the atoms
extracted from it are the concepts.

### Source pages and locators

A source may be *authored* as a full page, so an artifact you have something to say about
gets prose, a summary and its own edges rather than existing only as a citation string:

```
---
type: source
medium: paper          # paper|web|book|slides|video|transcript|notebook|code|data|audio|note|document
locator: raw/attention.pdf
author: Vaswani et al.
date: 2017
---
```

`locator` identifies the artifact and is format-agnostic: a repo-relative file, an
`http(s)://` URL, or a `doi:` / `arxiv:` / `isbn:` / `issn:` / `urn:` / `hdl:` identifier.
`medium` is inferred from the locator when omitted.

A `## Sources` bullet resolves, in order: an explicit `[[link]]` to an authored source
page; a locator that an authored source page declares; otherwise a generated stub node.
One artifact is therefore always one node, however it is referenced.

**`edges`** — every node carries its own outgoing edges as a list of
`{target, type, via, weight, context}`. This is the canonical carrier: relationships live in the graph as
structured typed edges, **not** as `[[markup]]` reproduced inside the prose. Accordingly, the
`summary`/`explanation` text is stored with link markup stripped to plain names (`BERT`, not
`[[BERT]]`) — the link itself is the corresponding edge.

**Additional concept-node fields:**

- `in_degree` / `out_degree` — count of incoming / outgoing **semantic** edges. Hub edges
  (`indexes`, `records`) are *excluded* so the index pointing at every node doesn't inflate the
  numbers. `in_degree` measures how depended-upon a node is; `out_degree` how much it asserts.
- `degree_by_type` — `{"in": {type: n}, "out": {type: n}}`, the full per-edge-type breakdown
  (includes hub edges), for finer analysis (e.g. "how contested" = incoming `contradicts`).
- `word_count` — length of summary+explanation (a rough content-density signal).
- `n_sources` — number of citations in `## Sources`.
- `aliases` — the strings that resolve to this node (title + filename stem).

Candidate fields worth adding later (not yet emitted): computed centrality (PageRank/
betweenness — done on load, not baked in to avoid staleness), a stable UUID, `created`/`updated`
timestamps, and a `domain`/cluster label once communities are detected.

## 3.1a `kind` classification of this reference wiki

Best-effort classification the parser reads from each page's frontmatter (26 concept nodes):

| kind | count | members |
|------|-------|---------|
| `concept` | 10 | Attention Mechanism, Self-Attention, Autoregressive Language Model, Few-Shot Learning, In-Context Learning, Emergent Capabilities, Scale and Scaling, Foundation Models, Homogenization, Alignment |
| `schema` | 9 | Transformer, Encoder-Decoder Architecture, Scaled Dot-Product Attention, Multi-Head Attention, Positional Encoding, Layer Normalization, BERT, GPT-3, Chinchilla |
| `procedure` | 6 | Masked Language Modeling, Next Sentence Prediction, Pre-training and Fine-tuning, RLHF, Reward Modeling, Proximal Policy Optimization |
| `fact` | 1 | Compute-Optimal Scaling |

Guidance used: **schema** = a concrete architecture, formula, or model structure; **procedure**
= a training/optimization process you carry out; **fact** = an empirical finding/law; **concept**
= an abstract idea, property, or category. Debatable calls: the named models (BERT/GPT-3/
Chinchilla) are classed `schema` as concrete architectures — a future `model`/`artifact` kind
could split these out; `Autoregressive Language Model` is a category so it stays `concept`.

### 3.2 Edge types (all directed; some are semantically symmetric)

| Type | From → To | Derived from | Directed? | Meaning |
|------|-----------|--------------|-----------|---------|
| `mentions`    | concept → concept | `[[link]]` in **Summary** or **Explanation** (or any non-special section) | yes | contextual reference in the body |
| `related`     | concept → concept | `[[link]]` in **Related** | symmetric | undirected association |
| `contradicts` | concept → concept | `[[link]]` in **Contradictions / tensions** | symmetric | flagged conflict/tension |
| `cites`       | concept → source  | each bullet in **Sources** | yes | provenance |
| `indexes`     | index → concept   | any `[[link]]` in `index.md` | yes | navigational membership (hub) |
| `records`     | log → concept     | any `[[link]]` in `log.md`   | yes | concept touched by a compilation/lint event |

`indexes` and `records` are **hub edges**: they are excluded from orphan detection (§6) and
from the DAG check, so the index pointing at every concept doesn't mask true orphans or create
false structure. A concept-level analysis simply filters edges to
`{mentions, related, contradicts, cites}`.

Edge properties: `type`, `via` (the section that produced it), `directed` (bool), `weight`,
`context`.

**`context` — the stated reason.** The bullet or paragraph the link sits in, markup stripped and
capped at 400 characters. An edge without it records *that* two pages are related and discards the
author's statement of *how*, which is usually the only part a reader wants:

```
- [[Zero-Shot Prompting]] — Brown 2020 makes demonstrations the flagship capability;
  DeepSeek-R1 reports they "consistently degrade its performance".
```

Two things are deliberately excluded. A leading `[[X]] — ` is the bullet's subject and is already
carried as the edge's target, so it is dropped. And a block that is only links
(`[[a]] · [[b]] · [[c]]`) has no prose, so its edges get `context: ""` rather than a list of
sibling names. An empty `context` is therefore a real signal: **that link was never given a
reason.** When merging duplicate edges, the longest context wins.

### The subject rule in typed sections

In a typed-relation section, a bullet's **leading link is what the bullet is about**; links
inside its prose are evidence cited in passing.

```
- [[Zero-Shot Prompting]] — [[GPT-3]] makes demonstrations the flagship capability;
  [[DeepSeek-R1]] reports they degrade performance.
```

That is one `contradicts` edge to Zero-Shot Prompting, plus `mentions` to GPT-3 and
DeepSeek-R1. Typing all three as `contradicts` would assert that this page disagrees with two
papers it is merely citing — and would give all three an identical context, since they share a
sentence. On one corpus this rule removed 60 of 104 `contradicts` edges as spurious.

The demotion requires the bullet to have *both* a leading link *and* prose after it. A bare
list (`- [[a]] · [[b]] · [[c]]`) and a prose paragraph both stay fully typed, so the older
paragraph-style convention is unchanged.
Symmetric edges are stored once with `directed: false`; consumers may add the reverse.

**`weight` — meaning, determination, use, update.**
- *Meaning:* the multiplicity of a typed relation — how many times node A links node B **in the
  same role**. If GPT-3's body references BERT twice, the `mentions` edge `gpt-3 → bert` has
  `weight: 2`. It is a lightweight proxy for "how strongly A leans on B" in that role.
- *Determined:* at build time. `links_in()` counts occurrences of each target within a section;
  `add_edge()` merges duplicate `(source, target, type)` triples, summing their counts. So one
  edge per (source, target, type), with `weight` = total occurrences.
- *Used:* it is carried into `graph.json`, SQLite, and GraphML. **Currently the `analyze`
  metrics treat edges as unweighted (binary presence)** — `weight` is available for consumers
  but does not yet drive PageRank/degree. Making the metrics weight-aware is a one-line change
  (opt-in) once we decide weight should mean "strength."
- *Updated:* the graph is **fully recomputed from the markdown on every `build`** — weights are
  re-derived, never mutated in place. This is a static, authored graph: there is no runtime
  decay or Hebbian reinforcement (that would be a MangroveMemory-style mechanic, deliberately
  out of scope here).

### 3.3 Section → edge-type map (default, case-insensitive)

```
contains "contradict" or "tension"  → contradicts
starts with "related"               → related
starts with "source"                → cites          (targets are source nodes)
"summary" | "explanation" | other   → mentions
```

The map is overridable (`--map map.json`) so wikis with different section names still parse.

## 4. Link resolution

1. Build a `title → id` table from all concept files (both the H1 title and the filename stem
   are registered as aliases, case-insensitive).
2. `[[Target]]` and `[[Target|alias]]` both resolve on `Target`.
3. Links inside inline code spans (`` `[[x]]` ``) are ignored.
4. Unresolved targets are recorded in `meta.warnings.dangling`. With `--stubs`, a
   `type:"missing"` node is created instead of dropping the edge.
5. Duplicate `(source, target, type)` edges are merged, incrementing `weight`.

## 5. Output format — decision

**Canonical output: a single `graph.json` in node-link form.** Rationale:

- **Graph-algorithm ready.** It loads directly into NetworkX
  (`networkx.readwrite.json_graph.node_link_graph`), D3, and Cytoscape.js — so
  centrality/traversal/community detection are one line away. This is what "traversable by
  graph algorithms" concretely requires.
- **Durable & diffable.** Plain text, git-friendly, human-inspectable — same virtues that make
  the wiki itself durable, and matching the existing KST `domain.json` precedent so this graph
  can feed that toolkit.
- **Schema-flexible.** Heterogeneous node/edge properties are trivial in JSON; they are painful
  in a columnar format.

**Rejected: Parquet.** Columnar Parquet is built for large, homogeneous analytical tables. A
knowledge graph is small, heterogeneous, and relational; Parquet gives up human-readability and
graph-native loading for compression we don't need at this scale.

**Optional companion emitters** (same data, different consumers):

- `--emit sqlite` → a single-file `graph.db` with `nodes` and `edges` tables. Enables SQL and
  **recursive-CTE traversal** without any library — the "executable, queryable" story.
- `--emit graphml` → `graph.graphml` for Gephi / yEd / igraph visual analysis.

SQLite and GraphML are *views* of the same graph; `graph.json` is the source of truth.

### 5.1 `graph.json` schema

```json
{
  "directed": true,
  "multigraph": true,
  "meta": {
    "generator": "wiki_to_graph/0.1",
    "generated": "<iso8601>",
    "source_dir": "<path>",
    "counts": {"concept": 26, "source": 6, "edges": {"mentions": 0, "related": 0, "contradicts": 0, "cites": 0}},
    "warnings": {"dangling": [["Source Page","Missing Target"]], "orphans": []}
  },
  "nodes": [
    {"id": "gpt-3", "type": "concept", "kind": "concept", "title": "GPT-3",
     "summary": "GPT-3 ... is a 175B decoder-only Autoregressive Language Model ...",
     "explanation": "GPT-3 keeps only the decoder half of the Encoder-Decoder Architecture ...",
     "sources": ["raw/03_gpt3.md (Brown et al., 2020)"],
     "file": "GPT-3.md", "in_degree": 7, "out_degree": 14,
     "edges": [
       {"target": "autoregressive-language-model", "type": "mentions", "via": "Summary",
        "weight": 1, "context": "Self-attention is the core computation of the Transformer…"},
       {"target": "bert", "type": "contradicts", "via": "Contradictions / tensions",
        "weight": 1, "context": "BERT uses bidirectional self-attention; GPT-3 uses masked…"}
     ]}
  ],
  "links": [
    {"source": "gpt-3", "target": "bert", "type": "contradicts",
     "via": "Contradictions / tensions", "directed": false, "weight": 1,
     "context": "BERT uses bidirectional self-attention; GPT-3 uses masked (left-to-right)…"}
  ]
}
```

Note the text is plain (`Autoregressive Language Model`, not `[[Autoregressive Language Model]]`)
— that relationship appears as an entry in `edges`. `edges` (on each node) is the canonical
representation; the top-level `links` array is the same set flattened for NetworkX/D3/Cytoscape
(the NetworkX-default key), generated from the node edges — a convenience mirror, not a second
source of truth.

### 5.2 SQLite schema (when `--emit sqlite`)

```sql
CREATE TABLE nodes (id TEXT PRIMARY KEY, type TEXT, title TEXT, summary TEXT,
                    explanation TEXT, sources TEXT, file TEXT,
                    in_degree INT, out_degree INT);
CREATE TABLE edges (src TEXT, dst TEXT, type TEXT, via TEXT,
                    directed INT, weight INT,
                    FOREIGN KEY(src) REFERENCES nodes(id),
                    FOREIGN KEY(dst) REFERENCES nodes(id));
-- Example: all concepts reachable from 'gpt-3' following mentions/related edges
WITH RECURSIVE reach(id) AS (
  SELECT 'gpt-3'
  UNION
  SELECT e.dst FROM edges e JOIN reach r ON e.src = r.id
  WHERE e.type IN ('mentions','related')
) SELECT * FROM reach;
```

## 6. Validation rules

Run after every build:

1. **Unique ids** — no two pages slug to the same id.
2. **Dangling links** — every `[[link]]` resolves (or is stubbed). Reported, non-fatal.
3. **Orphans** — concept nodes with `in_degree + out_degree == 0`. Reported.
4. **Self-loops** — a page linking to itself. Reported, dropped.
5. **Acyclicity (opt-in)** — over a chosen directed edge subset (`--dag-edges mentions`),
   report whether the subgraph is a DAG and list any strongly-connected components. `related`
   and `contradicts` are inherently symmetric and are **not** expected to be acyclic.

## 7. Optional: knowledge-space projection

With `--kst`, additionally emit a `domain.json` compatible with the borrowed KST toolkit:
`items` = concepts (carrying `id`, `name`, `description` = Summary), `prerequisites` = a chosen
directed edge subset (default `mentions`). These are **candidate** prerequisites derived
heuristically from body references — they must be curated before being treated as a true KST
surmise relation. This is the bridge from "knowledge graph" to "knowledge space."
