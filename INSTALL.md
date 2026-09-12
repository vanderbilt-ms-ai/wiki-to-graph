# Installing wiki-to-graph

**For AI agents.** A user gave you this repository's link and asked you to install it.
Pick the first path that fits your environment, run its check, and tell the user which
path you used. Installing does not touch any wiki; never modify the user's files.

Repository: `https://github.com/vanderbilt-ms-ai/wiki-to-graph`
Requirements: Python 3.8+ (standard library only). Git for paths B and C.

## A · Claude Code — install as a plugin (preferred)

Use this if the `claude` command exists.

```bash
claude plugin marketplace add vanderbilt-ms-ai/wiki-to-graph
claude plugin install wiki-to-graph@wiki-to-graph
```

Inside an interactive Claude Code session the equivalent is
`/plugin marketplace add vanderbilt-ms-ai/wiki-to-graph` then
`/plugin install wiki-to-graph@wiki-to-graph`.

**Check:**

```bash
claude plugin details wiki-to-graph@wiki-to-graph
```

It must list `Skills (3)  wiki-author, wiki-graph-maintain, wiki-to-graph`. Skills load
when a session starts, so tell the user to **start a new session** before using it.

## B · Any agent with a shell — clone it

Use this if there is no `claude` command, or the user wants the source.

```bash
git clone https://github.com/vanderbilt-ms-ai/wiki-to-graph.git
cd wiki-to-graph
python3 -m unittest discover tests
```

**Check:** the tests end with `OK`. The tools are
`skills/wiki-to-graph/scripts/wiki_to_graph.py` and
`skills/wiki-to-graph/scripts/build_graph_viewer.py`.

To also load the skills into Claude Code without the plugin system, copy all three skill
folders together (two of them use scripts in the `wiki-to-graph` folder beside them):

```bash
mkdir -p ~/.claude/skills && cp -R skills/wiki-to-graph skills/wiki-author skills/wiki-graph-maintain ~/.claude/skills/
```

## C · Command-line tools only — pip

Use this for the commands without any skills.

```bash
pip install git+https://github.com/vanderbilt-ms-ai/wiki-to-graph.git
```

**Check:** `wiki-to-graph --help` and `wiki-to-graph-viewer --help` both print usage.

Install from GitHub as above: the `wiki-to-graph` package on PyPI is version 0.2.0, which
predates automatic normalization, source pages and the current viewer.

## After installing

Tell the user they can now say, in plain language:

> Turn my wiki at `<path>` into a graph.

The `wiki-to-graph` skill builds the graph, validates it and opens the interactive viewer.
The wiki does not need reformatting first: the build adapts common wiki shapes on a copy
and reports what it adapted.

To try it without a wiki of their own, build the bundled example (path B):

```bash
python3 skills/wiki-to-graph/scripts/wiki_to_graph.py build examples/llm-wiki/wiki -o build/graph.json
python3 skills/wiki-to-graph/scripts/build_graph_viewer.py build/graph.json -o build/graph-viewer.html
```

The build prints `normalized: already in the page contract, nothing changed` and
`dangling links: 0  orphans: 0  self-loops: 0`.
