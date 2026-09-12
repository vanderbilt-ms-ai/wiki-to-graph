---
name: wiki-author
description: >-
  Build an LLM wiki from scratch out of a pile of artifacts, so that it produces a
  clean typed knowledge graph on the first build. Use when the user has source
  material but no wiki yet — "build a wiki from the papers in raw/", "turn these
  PDFs into a wiki", "make entity pages from these documents", "create an LLM wiki
  from this folder", "read these papers and make a knowledge base", "turn this
  course material / these transcripts / this documentation into a wiki". Covers
  what earns a page, the exact page contract, how to write links so the reason
  survives into the graph, and the lint/build/validate gate to pass before
  claiming the wiki is done. Once the wiki exists, wiki-to-graph builds and
  analyses the graph and wiki-graph-maintain keeps it healthy as it grows.
---

# Authoring a wiki that graphs cleanly

A wiki can be well written and still produce a graph that is useless to query. The
defects are invisible in the markdown and irreversible-looking once built:

| Written like this | Produces |
|---|---|
| `- [[a]] · [[b]] · [[c]]` under `## Related` | valid edges that explain nothing |
| a paper as a concept page | an artifact misfiled as a unit of knowledge |
| all disagreements on one `contradictions.md` | a hub joined to everything, and concepts joined to nothing |
| `README.md` as the index | no hub node at all — README is excluded by default |
| no `## Sources` | claims the graph cannot trace |

`SCRIPT=skills/wiki-to-graph/scripts/wiki_to_graph.py` throughout.

## 1. Sources first, concepts second

Every artifact becomes a **source page**, never a concept page. A paper is not a
unit of knowledge — it *contains* units of knowledge.

```
python3 $SCRIPT update <wiki> add-source --title "<short name>" \
  --locator <path|URL|doi:…|isbn:…> [--medium …] [--author …] [--date …]
```

Do this for every artifact before writing a single concept page. It gives you the
citation targets the concept pages need, and it forces the inventory to be explicit.

## 2. Say what earns a page — out loud, before writing

Write down the threshold and show the user the candidate list and its count
**before** creating files. A threshold you did not state is one you hid.

A workable default: a term earns a page if **two or more artifacts use it as a
load-bearing idea**, or if **one introduces it and a later one disputes it**. Skip
terms that appear once with no downstream use.

Assign each candidate a `kind`:

| kind | holds |
|---|---|
| `concept` | an abstract idea, property or category |
| `schema` | a concrete structure, formula or architecture |
| `procedure` | a process, method or technique |
| `fact` | an empirical finding or result |

## 3. The page contract

```markdown
---
kind: concept | schema | procedure | fact
---

# Title

## Summary
One to three sentences. What it is, and why it is in this collection.

## Explanation
The substance. Every number and every causal claim names the artifact it came from.
If a figure is not in the artifact, say so — never estimate.

## Related
- [[Other Page]] — one line on why these two belong together.

## Contradictions / tensions
- [[Other Page]] — both claims in their own words, and what a reader should conclude.

## Sources
- raw/file.pdf — Citation (Author, Year)
```

The index is **`index.md`**, not `README.md`. Its bullets get a reason too.

## 4. How you write a link decides what the graph knows

This is the rule that most affects whether the result is usable.

**One link per bullet, and state the reason.** The text after the link becomes the
edge's `context` — in a graph viewer it is the *only* part of the relationship a
reader sees. A bare list types every link and explains none:

```markdown
## Related
- [[in-context-learning]] · [[zero-shot-prompting]]          ← no reason; don't
- [[in-context-learning]] — few-shot is the demonstration-bearing case of it
- [[zero-shot-prompting]] — the same interface with the demonstrations removed
```

**Lead with the page the bullet is about.** Links inside the prose are evidence and
are typed `mentions`, not the relation:

```markdown
- [[Zero-Shot Prompting]] — [[GPT-3]] makes demonstrations the flagship capability;
  [[DeepSeek-R1]] reports they degrade performance. A reversal, not a qualification.
```

That is one `contradicts` edge to Zero-Shot Prompting. Writing the same sentence as
a paragraph with no leading link types all three as `contradicts`, asserting
disagreement with two papers that were only cited.

**Put each disagreement on both pages that disagree.** A central `contradictions.md`
is worth keeping for narrative, but if the tension lives *only* there, the two
concepts that actually disagree are not connected to each other.

**Only call it a contradiction if both sides cite an artifact and cannot both be
true.** Different benchmark, different model generation or different scope is a
scope dispute: record it as `related` and explain the difference.

## 5. Gate before you build

```bash
python3 $SCRIPT lint <wiki>
```

`lint` reads the markdown, not the graph, and catches what `validate` structurally
cannot: unexplained links, ambiguous bullets, missing `kind:`, missing `## Sources`,
a missing `index.md`, sources with no locator, and disagreements piled on one hub.

Fix every `error`. Work the `warn` list down — do not explain it away. `--strict`
makes warnings fail, which is the right setting for a wiki you will hand to someone.

## 6. Build, validate, look

```bash
python3 $SCRIPT build  <wiki> -o build/graph.json --emit sqlite,graphml
python3 $SCRIPT validate build/graph.json
python3 $SCRIPT query    build/graph.json unexplained
python3 skills/wiki-to-graph/scripts/build_graph_viewer.py build/graph.json -o build/graph-viewer.html
```

`validate` must print `RESULT: PASS`. Then **open the viewer and click three nodes.**
Every check above can pass on a wiki whose pages misread their sources; reading three
of them is the only step that catches it.

## Before telling the user it is done

- `lint` shows zero errors, and you have reported the remaining warning count.
- `validate` prints `RESULT: PASS`.
- Every page has at least one inbound link.
- Every concept page cites at least one source.
- Open two artifacts and check the pages citing them still say what they say.

Report: the page count, the threshold you used, two terms you left out and why, the
number of links still lacking a stated reason, and what you are least sure about.
A script can prove every link resolves. It cannot tell you a page misread its source.
