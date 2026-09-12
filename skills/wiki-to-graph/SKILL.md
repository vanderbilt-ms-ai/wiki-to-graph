---
name: wiki-to-graph
description: >-
  Turn an LLM wiki (a folder of markdown pages linked with [[wiki-links]], in the
  Karpathy "LLM wiki" pattern) into a typed, queryable knowledge graph and an
  interactive browser view — whatever shape the wiki is in. Use whenever the user
  wants to turn a wiki / vault / folder of interlinked markdown notes into a graph,
  knowledge graph, or knowledge space: "turn my wiki into a graph", "build a
  knowledge graph from these notes", "visualize my wiki", "make it queryable",
  "export to networkx / GraphML / SQLite", "compute centrality / find clusters /
  shortest path over my notes". Produces graph.json (NetworkX-compatible), optional
  SQLite and GraphML, an optional KST domain.json, and an offline HTML viewer.
---

# Wiki → Knowledge Graph

**Turning a wiki into a graph is one step: build it, then show it.** Do not ask the
user to reformat, fix, or tidy their wiki first. `build` normalizes a copy of the
wiki before parsing it — the user's files are never modified — so a wiki written
with a README for an index, `**Type:**` lines instead of frontmatter, papers written
up as pages, every disagreement on one hub page, and no Sources sections builds the
same graph as the same content written to the page contract.

The scripts are in `scripts/` inside this skill's base directory, however it was installed
(plugin, skills folder, or a clone). After a pip install, use the `wiki-to-graph` and
`wiki-to-graph-viewer` commands instead.

```bash
S="<this skill's base directory>/scripts"
python3 $S/wiki_to_graph.py build <wiki_dir> -o build/graph.json --emit sqlite,graphml
python3 $S/wiki_to_graph.py validate build/graph.json
python3 $S/build_graph_viewer.py build/graph.json -o build/graph-viewer.html
```

Then open `build/graph-viewer.html` for the user, and report:

- the node and edge counts by type, **quoted from the build output**,
- the `normalized:` line verbatim, so they can see what was adapted,
- `validate`'s `RESULT` line.

That is the whole job for a build. Everything below is reference.

## Answering questions in conversation

Many users never see a command line; the conversation is their only interface to the graph
(`docs/user-guide.md` is written for them). Answer in plain language, from the graph:

| The user asks | Run | Answer with |
|---|---|---|
| "tell me about X" | `query graph.json node "X"` | summary, kind, sources, relations grouped by type |
| "what is related to X, and why" | `query graph.json neighbors "X"` and `backlinks "X"` | each relation with its reason |
| "how is X connected to Y" | `query graph.json path "X" "Y"` | every hop, its edge type and reason |
| "what can I reach from X via related" | `query graph.json bfs "X" --edges related` | the pages, nearest first |
| "what are the contradictions" / "what disagrees with X" | `query graph.json contradicts` | both sides and the stated disagreement |
| "which sources does X cite" / "which pages use source S" | `neighbors "X" --edges cites` / `backlinks "S" --edges cites` | the sources or pages |
| "most central", "most contested", "main themes" | `analyze graph.json --top 10` | PageRank, in-degree, contested nodes, communities — quoted |
| "list every procedure" (or fact, schema, concept) | `query graph.json list --kind procedure` | the pages |
| "which links have no reason" | `query graph.json unexplained` | the pairs |
| "open the viewer on X" | open `graph-viewer.html#X` | — |
| "add this paper / page / link", rename, remove | `update …`, or the `wiki-graph-maintain` skill for new sources | rebuild, then report what changed |

The **reason** for a relationship is the edge's `context` field in `graph.json` — the sentence the
link was written in. Quote it; do not paraphrase it into something stronger. If a relationship is
not in the graph, say so and offer to add it to the wiki — never describe one the graph does not
contain. Edits go to the wiki's markdown, followed by a rebuild; never edit `graph.json`.

## What `build` normalizes automatically

| The wiki has | `build` does |
|---|---|
| `README.md` and no `index.md` | treats it as the index hub |
| a `**Type:** X` line, no frontmatter | derives `kind` (concept / schema / procedure / fact) from it |
| a page describing a paper, book, video, site, deck… | makes it a `source` node, with its locator from a `**File:**`-style field |
| a concept page with no Sources section | lists the source pages it links to as its Sources |
| one contradictions page of `### item` + `- [[side]]: claim` bullets | records every opposing pair on both pages that disagree, lists the competing claims on each topic the item names, and makes the hub an index |
| a page with no `# title` | takes the title from the filename |

And the parser reads these as written:

| Written like this | Read as |
|---|---|
| `## See also`, `## Tensions`, `## References` | Related, Contradictions, Sources |
| `- [[A]] — because [[P]] found X` | one relation to A; P is mentioned as evidence |
| `A contrasts with [[B]], unlike [[C]]` in a disagreement section | one disagreement with B; C is mentioned |
| `- **vs [[A]]:** …` | one disagreement with A |
| `None across the sources — see [[A]]` | no disagreement |
| `raw/a.md (X); raw/b.md (Y)` on one line | two citations |

The rules are in `scripts/wiki_normalize.py` and `references/spec.md`. `--emit-normalized
DIR` keeps the normalized wiki so the user can see it; `--no-normalize` parses the
wiki exactly as written.

## Ontology (one screen)

- **Nodes:** `concept` (an entity page), `source` (an ingested artifact — a page with
  `type: source`, or a citation in `## Sources`), plus `index` and `log` hub nodes.
- **Two independent axes.** `type` is what a node *is*; `kind`
  (`concept|schema|procedure|fact`) is what a concept *knows*, and applies to concepts
  only. A paper is not a `fact` — it *contains* facts; it is a `source`, and the claims
  drawn from it are atoms that `cites` it. A web page, book, deck, transcript or repo is
  a `source` the same way.
- **Edges:** `mentions` (body links), `related` (`## Related`), `contradicts`
  (`## Contradictions / tensions`), `cites` (concept → source), and hub edges
  `indexes` / `records`. `related` and `contradicts` are symmetric. Every edge carries
  `context` — the sentence the link was written in.

## Output

Canonical output is **`graph.json`** in node-link form: it loads straight into
NetworkX / D3 / Cytoscape and is diffable in git. Optional views: `--emit sqlite`
(SQL + recursive-CTE traversal) and `--emit graphml` (Gephi / yEd); `--kst` writes a
Knowledge Space Theory `domain.json`.

## Subcommands

All stdlib-only — no numpy / scipy / networkx required.

```bash
# BUILD (normalizes a copy first), VALIDATE, VIEW
python3 $S/wiki_to_graph.py build <wiki_dir> -o graph.json --emit sqlite,graphml --kst
python3 $S/wiki_to_graph.py validate graph.json
python3 $S/build_graph_viewer.py graph.json -o graph-viewer.html

# ANALYZE: PageRank, in-degree, contested nodes, components, communities, shortest path
python3 $S/wiki_to_graph.py analyze graph.json --top 5 --path "GPT-3" "Layer Normalization"

# QUERY: list | node | neighbors | backlinks | kind | edgetype | contradicts | unexplained | path | bfs | dfs
python3 $S/wiki_to_graph.py query graph.json node "RLHF"
python3 $S/wiki_to_graph.py query graph.json bfs "Transformer" --edges related
python3 $S/wiki_to_graph.py query graph.json dfs "GPT-3" --edges contradicts --undirected

# LINT (optional): what build will normalize, plus content notes only an author can
# supply, such as a link given no reason. Never a precondition for building.
python3 $S/wiki_to_graph.py lint <wiki_dir>

# UPDATE: edit the source markdown, then rebuild
python3 $S/wiki_to_graph.py update <wiki_dir> add-node    --title "Mixture of Experts" --kind schema --summary "..."
python3 $S/wiki_to_graph.py update <wiki_dir> add-source  --title "Switch Transformer" --locator "arxiv:2101.03961"
python3 $S/wiki_to_graph.py update <wiki_dir> add-edge    --from "Mixture of Experts" --to "Transformer" --type related
python3 $S/wiki_to_graph.py update <wiki_dir> remove-edge --from "Mixture of Experts" --to "Transformer" --type related
python3 $S/wiki_to_graph.py update <wiki_dir> remove-node --node "Mixture of Experts"
python3 $S/wiki_to_graph.py update <wiki_dir> rename      --node "GPT-3" --title "GPT-3 (Brown et al., 2020)"
python3 $S/wiki_to_graph.py update <wiki_dir> set-kind    --node "GPT-3" --kind schema
python3 $S/wiki_to_graph.py update <wiki_dir> set-type    --node "GPT-3" --type source
```

Keeping a graph healthy as it grows — ingesting new artifacts, deduping — is the
**`wiki-graph-maintain`** skill. Writing a wiki from scratch is **`wiki-author`**.

### Search & traversal filters (query bfs/dfs/path/neighbors/backlinks)

- `--edges a,b` traverse ONLY these edge types · `--ignore-edges x,y` all EXCEPT these
- `--kind a,b` visit ONLY these node kinds · `--ignore-kind x,y` all EXCEPT these
- `--node-type concept,source,index,log` (structural) · `--ignore-node-type x,y`
- `--undirected` treat edges as undirected in bfs/dfs

## Non-negotiable: compute, don't reason

Never state node/edge counts, reachability, centrality, or acyclicity from
inspection. Run the script and quote its printed output; re-run after any edit.
For heavier algorithms, load the JSON:

```python
import json, networkx as nx
from networkx.readwrite import json_graph
G = json_graph.node_link_graph(json.load(open("graph.json")), edges="links")   # MultiDiGraph
concepts = [n for n, d in G.nodes(data=True) if d.get("type") == "concept"]
nx.pagerank(G.subgraph(concepts))
```

## KST projection

`--kst` emits a `domain.json` for the course-development `kst.py` (`items` = concepts,
`prerequisites` = the `--dag-edges` subset). Those prerequisites are **heuristic
candidates** from body references — curate them before treating them as a true KST
surmise relation.

## Custom ontologies

Section names beyond the built-in synonyms: `--map map.json` (`{"substring": "edge_type"}`).
A different kind or edge vocabulary: `--vocab vocab.json` — see `docs/custom-vocabulary.md`.
Use the two together: a custom `--map` without a matching `--vocab` builds a graph in
which every node reports as an orphan.
