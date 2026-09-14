# User guide: your wiki as a knowledge graph, through a conversation

This guide is for people who work with the graph **by talking to Claude** — no code, no
terminal. It explains what the graph contains, how to read the viewer, what you can ask, and
how to change things. Every example uses the wiki bundled with this repository, built from six
papers: *Attention Is All You Need*, BERT, GPT-3, *Foundation Models*, InstructGPT and Chinchilla.

- [Getting started](#getting-started)
- [What is in the graph](#what-is-in-the-graph)
- [Reading the viewer](#reading-the-viewer)
- [What you can ask](#what-you-can-ask)
- [Changing the graph](#changing-the-graph)
- [When something looks wrong](#when-something-looks-wrong)
- [Glossary](#glossary)

---

## Getting started

**1. Install it.** Give Claude this repository's link and say:

> Install https://github.com/vanderbilt-ms-ai/wiki-to-graph

If it installed as a plugin, start a new conversation afterwards so Claude loads it.

**2. Build your graph.** Tell Claude where your wiki is:

> Turn my wiki at `~/notes/llm-wiki` into a graph.

You do not need to tidy or reformat the wiki first. Claude builds the graph, checks it, and
opens the interactive viewer. It then tells you three things:

- **how many pages and relationships** it found, by type;
- **what it adapted** — a line starting `normalized:`. Wikis are written in many styles (a README
  used as the index, a `Type:` line at the top of each page, all disagreements gathered on one
  page). The builder reads a copy of your wiki in a standard form. **Your own files are never
  changed.** If the line says *already in the page contract, nothing changed*, your wiki was
  already in that form;
- **whether the graph is structurally sound** — no links to missing pages, no pages nothing
  connects to.

**3. Explore.** Click around the viewer, or just ask questions in the conversation.

---

## What is in the graph

A wiki is already a graph: each page is a **node**, and each link between pages is a
**relationship**. The builder makes those explicit and gives each one a type.

### Nodes: what a page *is*

| Node type | What it is | In the example |
|---|---|---|
| **concept** | a page about one idea — the knowledge itself | *Transformer*, *In-Context Learning*, *Scale and Scaling* |
| **source** | a page for something you read: a paper, web page, book, deck, video transcript, codebase | *Attention Is All You Need*, *Language Models are Few-Shot Learners* |
| **index** | a navigation page that lists other pages | *Wiki Index* |
| **log** | a record of when the wiki changed | *Compilation Log* |

**A paper is a source, not a fact.** A paper *contains* findings; the findings are written up as
concept pages, and those pages **cite** the paper. This keeps "what we know" separate from "where
we read it", so you can always ask where a claim came from.

### Kinds: what a concept *knows*

Every concept page has one of four kinds:

| Kind | Holds | In the example |
|---|---|---|
| **concept** | an abstract idea, property or category | *Alignment*, *Foundation Models* |
| **schema** | a concrete structure, formula or architecture | *Transformer*, *Self-Attention*, *GPT-3* |
| **procedure** | a process, method or technique | *RLHF*, *Masked Language Modeling* |
| **fact** | an empirical finding or result | *Compute-Optimal Scaling* |

Sources, indexes and logs have no kind — they are not units of knowledge.

### Relationships: how two pages connect

The type of a relationship comes from **where the link is written** on the page.

| Relationship | Means | Written in | Example |
|---|---|---|---|
| **related** | these two belong together | the page's *Related* section | *Transformer* — *Self-Attention*: "its core computation" |
| **contradicts** | these two disagree | the *Contradictions / tensions* section | *GPT-3* — *Chinchilla*: GPT-3 was undertrained; a 70B model beats it |
| **cites** | this page draws on that source | the *Sources* section | *Transformer* cites *Attention Is All You Need* |
| **mentions** | this page refers to that one in passing | anywhere in the body text | *Few-Shot Learning* mentions *Pre-training and Fine-tuning* |
| **indexes** / **records** | the index lists it / the log records it | the index and log pages | *Wiki Index* lists *BERT* |

**related** and **contradicts** work both ways: if A contradicts B, then B contradicts A.

### Every relationship keeps its reason

Each relationship stores **the sentence it was written in** — the author's own explanation of why
the two pages connect. When you ask Claude how two things are related, or click a relationship in
the viewer, that sentence is what you see. If a link was written with no explanation, the graph
says so rather than inventing one.

### Years and topics: when, and about what

Pages can also carry **a year** and **topics**, so you can ask what came when and what belongs to
which subject.

- **Year.** A source's year comes from its date, or from a title such as *"… (Vaswani et al.,
  2017)"*. An idea page usually has no date of its own; it takes **the earliest year of the
  sources it cites** — when your collection first records the idea — and the graph says so.
- **Topics.** A topic groups pages by subject, for example *Language models / Prompting*. The
  part before the slash is the **field**, so one wiki can hold unrelated fields side by side. A
  topic is a label for a group of pages, not a piece of knowledge. An idea page without topics
  takes the topic most of its sources share.

One sentence records one relationship. If the GPT-3 page's disagreements included
*"[[Chinchilla]] — [[Compute-Optimal Scaling]] shows GPT-3 was undertrained"*, the disagreement is
with **Chinchilla**, the page the sentence leads with. *Compute-Optimal Scaling* is cited as
evidence, so it counts as a *mention*, not as a second disagreement.

---

## Reading the viewer

Claude opens the viewer for you. It is a single file that works offline in any browser.

### Top bar

- **Counts** of pages and relationships.
- **Search** — type part of a page's name to jump to it.
- **Relationship toggles** — show or hide each relationship type. *cites* and *indexes* start
  hidden to keep the picture readable; turn them on to see sources and the index.

When pages have years or topics, a **second bar** appears:

- **colour by** — kind (the default), topic, field or year. The legend changes to match.
- **layout** — *timeline* lines pages up left to right by year, with undated pages in a strip on
  the left. A link that reaches far left points back in time.
- **topic** — show only one field or topic. Everything else is hidden and the map re-forms
  around what is left.
- **years** — show only pages from a range of years.

### The map

- **Colour** shows the kind (or type, for sources and hubs) — see the legend.
- **Size** shows how many pages point at a node: bigger means more depended-upon.
- **Line colour** shows the relationship type; red lines are disagreements, dashed lines are citations.
- **Scroll** to zoom, **drag the background** to pan, **drag a node** to move it, **fit** to reframe.
- **Click a node** to select it: its neighbours stay bright and everything else fades.

### The side panel

The **legend** stays at the top (collapse it with the ▾). Below it, for the selected page:

- **Title, kind, and counts** — how many relationships point in and out, how many sources it
  cites, how long the page is. For a source, its medium (paper, web, book…) and location.
- **Summary**, and the **full explanation** (click to expand), shown as the page's formatted text.
- **Sources** the page cites.
- **Mutual — holds in both directions**: *related* and *contradicts*, each listed once.
- **This page points to**: pages it mentions or cites.
- **Points at this page**: pages that mention or cite it.

Every relationship shows **its reason** under the page name. Two special notes can appear there:

- *from X's body text* — the link itself had no explanation, but one of the two pages discusses
  the other in its text, so that passage is shown instead.
- *no reason given* — neither page explains the connection. It is a real link, just an
  unexplained one.

Click any listed page to go to it; **← back** returns you.

**Linking to a page:** add its name to the viewer's address after `#` —
`graph-viewer.html#Transformer` opens with *Transformer* selected. You can also just ask Claude to
open the viewer on a page.

---

## What you can ask

Ask in your own words. Claude answers from the graph and quotes the reasons stored there. These
are examples, not commands to memorise.

### Exploring

- *"Tell me about the Transformer page."*
- *"What are the main themes in my wiki?"* — Claude groups pages into clusters of closely connected
  pages. A small wiki where everything links to everything may come back as a single cluster.
- *"Which pages are most central?"* — the pages the rest of the wiki depends on most.
- *"List every procedure in the graph."* — or schema, fact, concept.
- *"Open the viewer on RLHF."*

### Relationships

- *"What is related to In-Context Learning, and why?"*
- *"How is Positional Encoding connected to RLHF?"* — Claude walks the shortest chain of
  relationships between them and explains each step.
- *"What points at GPT-3?"*
- *"Starting from Transformer, what can I reach through related pages only?"*

### Time and topics

- *"What topics are in my wiki?"*
- *"Show me everything from 2020 to 2022, in order."*
- *"Which ideas first appear in 2025?"*
- *"Does the materials engineering material connect to anything else?"* — Claude lists the links
  between pages that share no topic. *None* is a real answer: two unrelated fields can sit in one
  wiki without touching.
- *"Open the viewer as a timeline, coloured by field."*
- *"Trace Cao 2026 back to Johnson and Cook 1983."* — Claude lists the chains of papers citing
  papers between the two, and which papers most chains pass through. This follows citations
  only; two papers about the same idea are not a chain.

### Disagreements

- *"What are all the contradictions in my wiki?"*
- *"What disagrees with GPT-3, and what does each side say?"*
- *"Which pages are the most contested?"*

### Sources and evidence

- *"Which sources does Scale and Scaling cite?"*
- *"Which pages draw on the Chinchilla paper?"*
- *"Where does the claim that GPT-3 was undertrained come from?"*

### Quality

- *"Which links in my wiki have no stated reason?"*
- *"Did anything need adapting when you built it?"*
- *"Is anything disconnected or broken?"*

---

## Changing the graph

The graph is **built from your wiki pages**. To change the graph, change the wiki; Claude makes
the edit and rebuilds. You can ask for any of these in plain language:

| You want to | Ask |
|---|---|
| add something you read | *"Add this paper to my wiki: `<link or file>`."* |
| add an idea | *"Add a page for Mixture of Experts, as a schema."* |
| connect two pages | *"Relate Mixture of Experts to Transformer — it replaces the feed-forward layer."* |
| record a disagreement | *"Record that Chinchilla contradicts GPT-3 on how much data a model needs."* |
| cite a source | *"Mark that Mixture of Experts cites the Switch Transformer paper."* |
| rename a page | *"Rename GPT-3 to GPT-3 (Brown et al., 2020)."* — links across the wiki are updated |
| remove something | *"Remove the link between X and Y"* or *"Delete the page Z."* |
| reclassify | *"Make Chinchilla a fact"* or *"This page is really a source, not a concept."* |
| set topics | *"Tag the GPT-3 paper with Language models / Scaling."* |

**Adding something you read** follows a careful routine: Claude makes a source page for it,
proposes the ideas worth their own pages and **shows you that list before writing anything**,
checks each against what the wiki already has so it does not create duplicates, writes the pages
with their reasons and citations, rebuilds, and tells you what changed.

**Always give a reason when you connect pages.** *"Relate A to B"* produces a link; *"Relate A to
B because…"* produces a link someone can understand later.

---

## When something looks wrong

**A relationship says "no reason given."** The wiki links the pages without explaining why. Ask
Claude to *"add a reason for the link between A and B: …"*, or ask it to list all such links.

**A relationship seems wrong.** The graph records what the pages say. Ask Claude to *"show me the
sentence that creates the link between A and B"*. If the page is wrong, fix the page; if the page
is right but the link was read wrongly, that is worth reporting as an issue.

**Disagreements appear between papers rather than ideas.** Your wiki probably recorded
disagreements on one central page, as *"paper A says X; paper B says Y"*. The builder places each
disagreement between the sides that hold it — here, the papers — and lists the competing claims on
the idea they are about, under *Disputed claims*. To see a disagreement between two ideas, write
it on those ideas' pages.

**A page I expected is missing.** Only `.md` files **directly inside** the wiki folder are read —
pages in subfolders are not included. If your wiki is organised into subfolders (common in
Obsidian vaults), ask Claude to build from a folder that holds all the pages at one level.

**Two pages mean the same thing.** Ask Claude to *"merge B into A"*: it renames or removes the
duplicate and updates the links, so the wiki keeps one page per idea.

**The numbers changed after a rebuild.** The graph is rebuilt from the wiki every time, so any
edit to the pages — yours or Claude's — can change the counts. Claude reports the counts after
every build; each build replaces the previous graph, so compare against the counts it gave you
before.

---

## Glossary

| Term | Meaning |
|---|---|
| **wiki** | the folder of linked markdown pages the graph is built from |
| **node** | one page in the graph |
| **relationship** (edge) | one typed connection between two pages |
| **type** | what a node is: concept, source, index or log |
| **kind** | what a concept knows: concept, schema, procedure or fact |
| **source** | something that was read — paper, web page, book, deck, transcript, code |
| **reason** (context) | the sentence a relationship was written in |
| **topic** | a label grouping pages by subject, written *Field / Topic* |
| **field** | the part of a topic before the slash; the broadest grouping |
| **year** | a source's date; for an idea page, the earliest year among the sources it cites |
| **mutual** | a relationship that holds both ways: related, contradicts |
| **normalized** | the builder read a copy of your wiki in a standard form; your files are untouched |
| **central** | depended on by many other pages |
| **contested** | involved in many disagreements |
| **cluster** | a group of pages more connected to each other than to the rest |
