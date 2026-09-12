# Using your own vocabulary

The default ontology — four kinds (`concept`/`fact`/`schema`/`procedure`) and four edge types
(`mentions`/`related`/`contradicts`/`cites`) — is deliberately small. It is not fixed.

Two independent switches:

| you want | use |
|---|---|
| different `##` section names → edge types | `--map map.json` (already supported) |
| different **kinds** and **edge types** | `--vocab vocab.json` (this page) |

## The trap `--vocab` exists to close

`--map` alone is not enough, and the failure is silent. Section names drive what edge types get
*created*; a separate set of constants drives which edge types *count*:

- `CONCEPT_EDGE_TYPES` — in/out degree at build time
- `CONCEPT_EDGE` — the analysis graph in `analyze`
- `ALL_EDGE_TYPES` — the traversal surface in `query`
- `KINDS` — an unrecognised `kind:` is coerced to `concept`

Build a wiki with custom section names and no vocabulary, and everything *looks* fine — the edges
are in `graph.json`, the counts are right — but every node reports degree 0:

```
$ wiki_to_graph.py build wiki -o g.json --map map.json
edges: {'part-of': 657, 'uses': 192, 'derived-from': 51, …}
orphans: 973                      # <- every node in the graph

$ wiki_to_graph.py build wiki -o g.json --map map.json --vocab vocab.json
edges: {'part-of': 657, 'uses': 192, 'derived-from': 51, …}     # identical
orphans: 40                       # <- the genuinely unconnected ones
```

`analyze` shows the same thing from the other side: without a vocabulary it considers **0 edges**,
so PageRank is uniform, every node is its own component, and community detection returns one
community per node.

## Format

Every key is optional; omitted keys keep the default.

```json
{
  "kinds":         ["object", "concept", "fact", "experience", "procedure", "…"],
  "concept_edges": ["part-of", "uses", "derived-from", "justified-by", "…"],
  "symmetric":     ["contradicts", "co-occurred-with"],
  "hub_edges":     ["indexes", "records"]
}
```

- **`kinds`** — permitted `kind:` frontmatter values. Anything else falls back to `concept`.
- **`concept_edges`** — the semantic edge types. This is the one people miss; it drives degree,
  analysis, and traversal.
- **`symmetric`** — edge types stored with `directed: false`. No edges are duplicated.
- **`hub_edges`** — excluded from degree so `index.md` pointing at everything does not inflate it.

Pass it to `build`, `validate`, `analyze`, and `query`. `analyze --edges` now defaults to the active
`concept_edges` rather than a hardcoded trio, so it needs no separate flag.

## Worked example

[`examples/vocab.custom.json`](../examples/vocab.custom.json) carries the nine knowledge primitives
and the Biolink-style relation hierarchy used by
[jarvis](https://github.com/mangrove-one/jarvis) and the Mangrove ecosystem graph:

```bash
wiki_to_graph.py build  wiki -o g.json --map map.json --vocab examples/vocab.custom.json \
                        --dag-edges part-of,is-a,requires,derived-from,preceded-by,supersedes
wiki_to_graph.py analyze g.json --vocab examples/vocab.custom.json
```

## The viewer

`build_graph_viewer.py` needs no flag — it derives its palettes and edge toggles from what the graph
actually contains, assigning colours to unknown kinds and edge types and defaulting them visible.
Previously its three inlined JS maps knew only the built-in vocabulary, so a custom graph rendered
as unconnected dots: every edge present in the data, none of them in the `enabled` map, so none
drawn.
