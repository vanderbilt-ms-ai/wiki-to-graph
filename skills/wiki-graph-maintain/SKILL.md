---
name: wiki-graph-maintain
description: >-
  Add to, edit, and maintain an existing wiki knowledge graph over time. Use
  when the user wants to ingest a new artifact into a wiki that already exists —
  a paper, web page, book, slide deck, transcript, video, codebase, report —
  or says "add this to the wiki", "add this source", "turn this into knowledge
  atoms", "fold this paper in", "update the graph", "keep the graph healthy",
  "find duplicates in my wiki", "what's orphaned", "prune the graph", "rename
  this concept everywhere". Covers the full loop: frame the artifact as a source
  node, extract candidate atoms, dedupe against what is already there, author
  pages, link them with typed edges, rebuild, validate, and report the delta.
  For a first build of a graph from a wiki that has none, use wiki-to-graph.
---

# Maintaining a wiki knowledge graph

`wiki-author` writes a wiki from artifacts; `wiki-to-graph` turns a wiki into a
graph. This one keeps it correct while it grows. The failure mode it exists to prevent is **silent degradation**:
a graph that accumulates near-duplicate concepts, uncited claims, and orphans
until its metrics stop meaning anything.

`SCRIPT=skills/wiki-to-graph/scripts/wiki_to_graph.py` throughout.

## The rule that makes the rest work

**The markdown is the single source of truth.** Never edit `graph.json` — it is
derived and every `build` recomputes it from the pages. All changes go through
`update` or a direct edit of the markdown, then a rebuild.

## The ingest loop

Run it in order. Steps 1–3 happen *before* any page is written.

### 1. Frame the artifact as a source

An artifact is not knowledge; it *contains* knowledge. It becomes a `source`
node, never a concept.

```
python3 $SCRIPT update <wiki> add-source --title "<short name>" \
  --locator <path|URL|doi:…|isbn:…> [--medium …] [--author …] [--date …]
```

`medium` is inferred from the locator when omitted (a URL gives `web`, `.pptx`
gives `slides`, `.vtt` gives `transcript`, `doi:` gives `paper`). Set it
explicitly when the inference would be wrong.

### 2. Propose atoms, and show the list first

Read the artifact. Draft a list of candidate atoms with a `kind` each:

| kind | holds |
|---|---|
| `concept` | an abstract idea, property or category |
| `schema` | a concrete structure, formula or architecture |
| `procedure` | a process, method or technique |
| `fact` | an empirical finding or result |

**Show the user the candidate list and the count before writing anything.** An
agent that writes 40 pages and then asks for review has already spent the
review. State the threshold you used for "this earns a page" — otherwise you
picked one and hid it.

### 3. Dedupe before you add — the step that actually matters

For every candidate, check whether the graph already covers it:

```
python3 $SCRIPT query <graph.json> list --kind <kind>
python3 $SCRIPT query <graph.json> node "<candidate title>"
python3 $SCRIPT query <graph.json> neighbors "<nearby concept>"
```

Then decide, per candidate:

- **Already there** → add the new source to that page's `## Sources` and extend
  its prose. Do not create a second page.
- **Already there under a worse name** → `update … rename --node <old>
  --title <better>`, which rewrites inbound links across the wiki, then extend.
- **Genuinely new** → create it in step 4.

A new page that restates an existing one is a regression. It splits the
in-degree of a real concept across two weaker nodes and quietly corrupts every
centrality number downstream.

### 4. Author the pages

```
python3 $SCRIPT update <wiki> add-node --title "<title>" --kind <kind> \
  --summary "<1–3 sentences>"
```

Then write `## Explanation` in the file. Every number and every causal claim
names the artifact it came from. If a figure is not in the artifact, say so —
do not estimate.

### 5. Link, with reasons

```
python3 $SCRIPT update <wiki> add-edge --from "<a>" --to "<b>" --type related
python3 $SCRIPT update <wiki> add-edge --from "<a>" --to "<b>" --type contradicts
python3 $SCRIPT update <wiki> add-edge --from "<a>" --to "<source>" --type cites
```

- Every atom `cites` at least one source. An uncited atom is an assertion.
- A link with no stated reason does not go in. Write it on the bullet:
  `- [[Other Page]] — one line on why`. The parser keeps that line as the edge's
  `context`, and it is the only part of the relationship a reader actually sees.
- **One link per bullet in a typed section.** In `- [[A]] — because [[P]] found X`, A is
  the relation and P is evidence: the parser types P as `mentions`, not as the relation.
  A bare `- [[a]] · [[b]] · [[c]]` line types every link and explains none.
- Only `contradicts` when both sides cite an artifact and **cannot both be
  true**. Different scope, different benchmark or different era is a *scope
  dispute* — record it as `related` and explain the difference. Promoting
  paraphrase to disagreement is the most common way these graphs go wrong.

### 6. Rebuild and validate

```
python3 $SCRIPT build    <wiki> -o build/graph.json --emit sqlite,graphml
python3 $SCRIPT validate build/graph.json
```

`build` normalizes structure itself (see the `wiki-to-graph` skill), so there is no
formatting to fix before building. `validate` must print `RESULT: PASS`. Dangling links,
orphans and self-loops are structural defects, not warnings to note and move past. A
`mentions` cycle is expected and is reported as info.

### 7. Report the delta

Give node and edge counts by type, before and after. Then state:

- which candidates were **merged** into existing pages rather than added,
- which were **left out**, and why,
- what you are **least sure about** — a misread source is invisible to every
  check above.

## Never state a metric you did not run

Do not assert node counts, edge counts, degree, centrality, reachability,
acyclicity or community structure from reading the markdown. Run the script and
quote its output. This holds even when the number seems obvious.

## Health checks

Run periodically, and always after a bulk ingest:

```
python3 $SCRIPT lint     <wiki>                    # optional: content notes only an author can supply
python3 $SCRIPT validate build/graph.json          # dangling / orphans / self-loops
python3 $SCRIPT analyze  build/graph.json --top 10 # PageRank, in-degree, contested, communities
python3 $SCRIPT query    build/graph.json contradicts
python3 $SCRIPT query    build/graph.json unexplained
```

What to look for:

- **Unexplained links** — `query unexplained` lists typed links with no reason on the link
  and none in either page's body. Each asserts a connection the wiki never justifies. Write
  the reason or remove the link; do not invent one.
- **Orphans** — a concept nothing links to. Either link it or remove it.
- **A community that is one artifact's vocabulary** — a paper was ingested
  without connecting its atoms to what was already there. Add the cross-links.
- **`contradicts` concentrated on a hub page** — disagreements were recorded in
  one central page instead of on the pages that actually disagree. Push each one
  onto both sides; the hub keeps the narrative.
- **Two high-degree nodes that mean the same thing** — merge with `rename` plus
  `remove-node`.

## Removing things

```
python3 $SCRIPT update <wiki> remove-edge --from "<a>" --to "<b>" [--type related]
python3 $SCRIPT update <wiki> remove-node --node "<title>"
```

`remove-node` names every page that will dangle as a result. Fix each one it
lists, then rebuild — do not leave the wiki failing validation.

## Before telling the user you are done

- `validate` prints `RESULT: PASS`.
- Every page added in this pass has at least one inbound link.
- Every atom added in this pass `cites` a source.
- Open the artifact again and check two of the pages that cite it still say what
  it says. A script can prove every link resolves; it cannot tell you a page
  misread its source.
