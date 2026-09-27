---
name: wiki-graph-view
description: >-
  Open the interactive viewer for a wiki knowledge graph that already exists, in a
  browser, optionally focused on one page. Use when the user says "show me the graph",
  "open the viewer", "open the graph in the browser", "visualize my knowledge graph",
  "show Transformer in the graph", "take me to the RLHF node", or asks to look at the
  graph after a build or an ingest. Rebuilds the viewer (and the graph, if the wiki
  changed) so what opens is current, opens it at the right node, and serves it on
  localhost only when a browser tool cannot open local files. To build a graph from a
  wiki for the first time, use wiki-to-graph; to change the graph, use
  wiki-graph-maintain.
---

# Viewing a wiki knowledge graph

`wiki-to-graph` builds the graph and writes the viewer; `wiki-graph-maintain` keeps the
graph correct. This skill opens what they produced, so the user sees the current graph
at the page they asked about. The failure it prevents is **showing a stale graph**: a
viewer generated before the last edit, opened as if it were current.

`SCRIPT` is `wiki_to_graph.py` and `VIEWER` is `build_graph_viewer.py`, both in the
sibling `wiki-to-graph` skill -
`<this skill's base directory>/../wiki-to-graph/scripts/` - or the `wiki-to-graph` and
`wiki-to-graph-viewer` commands after a pip install.

## 1. Find the graph and make sure it is current

The graph is the `graph.json` the build wrote (`build/graph.json` unless the user built
it elsewhere). If there is none, there is nothing to view yet: build it with the
`wiki-to-graph` skill first.

The viewer shows `graph.json`, and `graph.json` shows the wiki as of the last build.
Check both links in that chain:

```bash
find <wiki_dir> -name '*.md' -newer build/graph.json | head -1     # wiki edited since the build?
[ build/graph-viewer.html -nt build/graph.json ] || echo stale      # viewer older than the graph?
```

- A page newer than `graph.json`: rebuild with the same options the graph was built with
  (`--vocab`, `--map` and `--emit` if it used them; ask if you do not know them), and
  check `validate` prints `RESULT: PASS`. A custom vocabulary graph rebuilt without its
  `--vocab` is a different graph.
- A viewer older than the graph, or none: regenerate it.

```bash
python3 $SCRIPT build <wiki_dir> -o build/graph.json [--vocab vocab.json --map map.json]
python3 $SCRIPT validate build/graph.json [--vocab vocab.json]
python3 $VIEWER build/graph.json -o build/graph-viewer.html
```

## 2. Open it

The viewer is one self-contained HTML file: fonts embedded, no network requests. Open the
file directly when you can.

| Where you are | Open with |
|---|---|
| macOS shell | `open "file://$(cd build && pwd)/graph-viewer.html#<Page>"` |
| Linux shell | `xdg-open "file://$(cd build && pwd)/graph-viewer.html#<Page>"` |
| Windows | `start "" "file:///C:/path/to/build/graph-viewer.html#<Page>"` |
| a browser tool that refuses `file://` | serve it on localhost (below) |

`#<Page>` selects a page on load: its title, its id (the kebab-case slug) or any alias,
matched case-insensitively. URL-encode spaces or quote the whole URL. Leave it off to
open the whole map.

### Serving it on localhost

Some agent browsers cannot open local files. Serve **only the viewer**, bound to the
loopback address:

```bash
mkdir -p build/viewer && cp build/graph-viewer.html build/viewer/index.html
python3 -m http.server 8765 --bind 127.0.0.1 --directory build/viewer
```

Then navigate to `http://127.0.0.1:8765/#<Page>`.

Why not serve `build/`: `http.server` exposes every file in the directory it serves, so
serving `build/` would also serve `graph.json`, `graph.db` and anything else there - the
whole wiki's content. Without `--bind 127.0.0.1` it listens on every network interface,
so other machines on the network can read it. A wiki of private notes needs both
precautions. Stop the server when the user is done.

## 3. Confirm it rendered

Check what actually opened before describing it: read the page's text (the header shows
`<n> nodes - <m> edges`, which must match the build output) or take a screenshot. If a
node was requested, confirm the side panel shows that page. Do not describe what you did
not see; if the browser cannot be inspected, say it was opened and not checked.

## 4. Tell the user how to read it (briefly, first time only)

- Scroll to zoom, drag the background to pan, drag a node to move it, `fit` to reframe.
- Click a page: its summary, full explanation and sources, and its outgoing edges and
  backlinks grouped by edge type, each with the reason the link was made. `<- back`
  retraces.
- Click an edge: its type, its direction and the reason written for it.
- Nodes are coloured by kind and edges by type; toggles hide edge types. When pages carry
  topics or years, a second bar colours by topic, field or year, filters by topic and year
  range, and switches to a timeline layout.
- **About this graph** explains all of it using this graph's own counts.

## Before telling the user it is open

- The viewer is newer than `graph.json`, and `graph.json` is newer than every wiki page -
  or you said which is stale and why you did not rebuild.
- `validate` printed `RESULT: PASS` for the graph being shown.
- The node count on screen matches the build output.
- If you started a server, it serves only the viewer, on `127.0.0.1`, and you told the
  user it is running.
