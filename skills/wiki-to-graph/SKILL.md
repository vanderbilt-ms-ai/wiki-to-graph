---
name: wiki-to-graph
description: >-
  Translate an LLM wiki (a folder of markdown entity pages linked with
  [[wiki-links]], in the Karpathy "LLM wiki" pattern) into a durable, typed,
  executable knowledge graph that graph algorithms can traverse. Use whenever
  the user wants to turn a wiki / vault / folder of interlinked markdown notes
  into a graph data structure, knowledge graph, or knowledge space — phrases
  like "turn this wiki into a graph", "make it queryable", "build a knowledge
  graph from these notes", "export to networkx / GraphML / SQLite", "compute
  centrality / find clusters / shortest path over my notes". Produces a
  canonical graph.json (NetworkX-compatible) plus optional SQLite and GraphML,
  and an optional KST domain.json projection.
---

# Wiki → Knowledge Space

**Authoring a wiki from scratch?** Use **`wiki-author`** first — it carries the page
contract and the link rules that decide whether this graph is worth querying.
**Keeping one healthy as it grows?** That is **`wiki-graph-maintain`**. This skill
turns an existing wiki into a graph and analyses it.

**Always `lint` before you `build`.** `validate` inspects a built graph and can only
see structural defects; `lint` reads the markdown and catches the authoring defects
that build cleanly and query uselessly — unexplained links, ambiguous bullets,
missing `kind:`, missing `## Sources`, a hub hoarding every disagreement.

```
python3 scripts/wiki_to_graph.py lint <wiki_dir> [--strict]
```

Turns the *implicit* graph in an LLM wiki (pages + `[[links]]`) into an
*explicit*, typed property graph you can run algorithms on. The trick: every
entity page uses the same sections, so **the section a link sits in determines
the edge type** — a link under `## Related` is a `related` edge, a link under
`## Contradictions / tensions` is a `contradicts` edge, and so on. The parse is
therefore deterministic.

Full ontology and format rationale: **`references/spec.md`** (read it before
extending the mapping). The "LLM wiki" pattern is due to Andrej Karpathy; see
Data Science Dojo's tutorial: https://datasciencedojo.com/blog/llm-wiki-tutorial/

## Ontology (one screen)

- **Nodes:** `concept` (an entity page), `source` (an ingested artifact — a page with
  `type: source`, or a citation in `## Sources`), plus `index` and `log` hub nodes.
- **Two independent axes.** `type` is what a node *is*; `kind`
  (`concept|schema|procedure|fact`) is what a concept *knows*, and applies to concepts
  only. A paper is not a `fact` — it *contains* facts; it is a `source`, and the claims
  drawn from it are `fact` atoms that `cites` it. Artifacts of any medium work the same
  way: a web page, book, deck, transcript or repo is a `source` with a `locator`.
- **Edges:** `mentions` (body links), `related` (`## Related`), `contradicts`
  (`## Contradictions / tensions`), `cites` (concept→source), and hub edges
  `indexes` / `records` from index/log. `related` and `contradicts` are symmetric.

## Output — decision

Canonical output is **`graph.json`** in node-link form: it loads straight into
NetworkX / D3 / Cytoscape, is diffable in git, and mirrors the KST `domain.json`
precedent. Parquet is deliberately **not** used (columnar, homogeneous,
non-graph-native — wrong tool for a small heterogeneous graph). Optional views:
`--emit sqlite` (SQL + recursive-CTE traversal) and `--emit graphml` (Gephi/yEd).

## Usage — six subcommands

Scripts live beside this file, in `scripts/` (i.e. `${CLAUDE_PLUGIN_ROOT}/skills/wiki-to-graph/scripts/`).
All are stdlib-only — no numpy/scipy/networkx required.

```bash
# 1) BUILD: parse a wiki folder into graph.json (+ optional views / KST projection)
python3 scripts/wiki_to_graph.py build <wiki_dir> -o graph.json --emit sqlite,graphml --kst

# 2) VALIDATE: structural check (exit 1 on defects). Dangling links, orphan concepts,
#    and self-loops fail; DAG cycles over cross-references are informational.
python3 scripts/wiki_to_graph.py validate graph.json

# 3) ANALYZE: PageRank, in-degree, contested nodes, components, communities, shortest path.
python3 scripts/wiki_to_graph.py analyze graph.json --top 5 --path "GPT-3" "Layer Normalization"

# 4) QUERY: canned questions — no raw SQL/graph code. Verbs:
#    list | node | neighbors | backlinks | kind | edgetype | contradicts | path | bfs | dfs
python3 scripts/wiki_to_graph.py query graph.json node "RLHF"
python3 scripts/wiki_to_graph.py query graph.json bfs "Transformer" --edges related
python3 scripts/wiki_to_graph.py query graph.json dfs "GPT-3" --edges contradicts --undirected
python3 scripts/wiki_to_graph.py query graph.json path "Positional Encoding" "RLHF"

# 5) UPDATE: edit the SOURCE wiki markdown, then re-run build. Actions:
python3 scripts/wiki_to_graph.py query  <graph.json> unexplained   # typed links nobody justified
python3 scripts/wiki_to_graph.py update <wiki_dir> add-node   --title "Mixture of Experts" --kind schema --summary "..."
python3 scripts/wiki_to_graph.py update <wiki_dir> add-source --title "Switch Transformer" --locator "arxiv:2101.03961"
python3 scripts/wiki_to_graph.py update <wiki_dir> add-edge   --from "Mixture of Experts" --to "Transformer" --type related
python3 scripts/wiki_to_graph.py update <wiki_dir> add-edge   --from "Mixture of Experts" --to "Switch Transformer" --type cites
python3 scripts/wiki_to_graph.py update <wiki_dir> remove-edge --from "Mixture of Experts" --to "Transformer" --type related
python3 scripts/wiki_to_graph.py update <wiki_dir> remove-node --node "Mixture of Experts"
python3 scripts/wiki_to_graph.py update <wiki_dir> rename     --node "GPT-3" --title "GPT-3 (Brown et al., 2020)"
python3 scripts/wiki_to_graph.py update <wiki_dir> set-kind   --node "GPT-3" --kind schema
python3 scripts/wiki_to_graph.py update <wiki_dir> set-type   --node "GPT-3" --type source

Maintaining a graph over time — ingesting a new artifact, deduping against what exists,
health checks — is the **`wiki-graph-maintain`** skill.

# 6) VIEW: render an interactive, offline HTML graph
python3 scripts/build_graph_viewer.py graph.json -o graph-viewer.html
```

### Search & traversal filters (query bfs/dfs/path/neighbors/backlinks)

Filter on edge type, node type/kind, or any combination — include *or* exclude:

- `--edges a,b` traverse ONLY these edge types · `--ignore-edges x,y` traverse all EXCEPT these
- `--kind a,b` visit ONLY these node kinds · `--ignore-kind x,y` visit all EXCEPT these
- `--node-type concept,source,index,log` (structural) · `--ignore-node-type x,y`
- `--undirected` treat edges as undirected in bfs/dfs

BFS/DFS are the classic traversals (`bfs_order`/`dfs_order`); `path` is BFS shortest path.
For heavier algorithms, load `graph.json` into NetworkX (below).

The script is **stdlib-only** (no pip installs) and prints node/edge counts, the
dangling-link / orphan / self-loop report, and the DAG check. `index.md` and
`log.md` are included as hub nodes by default — pass `--exclude index,log,readme`
to drop them.

## Non-negotiable: compute, don't reason

Never state node/edge counts, reachability, centrality, or acyclicity from
inspection. Run the script and quote its printed output; re-run after any edit to
the wiki. To go further (PageRank, communities, shortest paths), load the JSON:

```python
import json, networkx as nx
from networkx.readwrite import json_graph
# loads as a MultiDiGraph (multigraph:true preserves parallel typed edges)
G = json_graph.node_link_graph(json.load(open("graph.json")), edges="links")
concepts = [n for n, d in G.nodes(data=True) if d.get("type") == "concept"]
nx.pagerank(G.subgraph(concepts))                                # centrality, etc.
```

## Loading into the borrowed KST toolkit

`--kst` emits a `domain.json` compatible with the course-development `kst.py`
(`items` = concepts, `prerequisites` = the `--dag-edges` subset). Those
prerequisites are **heuristic candidates** from body references — curate them
before treating them as a true KST surmise relation.

## Extending to any wiki

The section→edge map lives in `DEFAULT_MAP` in the script and is overridable with
`--map map.json` (`{"substring": "edge_type", ...}`), so a wiki with different
section names still parses. Keep pages single-concept and sections consistent and
the graph stays clean.
