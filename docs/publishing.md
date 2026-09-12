# Distribution & publishing

How to get `wiki-to-graph`, how to publish a new release, and where it's listed.

## Get it

See **Install** in the [README](../README.md#install), or give an agent the repository link and
ask it to install — it follows [`INSTALL.md`](../INSTALL.md). The methods, all verified:

```bash
# Claude Code plugin
claude plugin marketplace add vanderbilt-ms-ai/wiki-to-graph
claude plugin install wiki-to-graph@wiki-to-graph

# command-line tools
pip install git+https://github.com/vanderbilt-ms-ai/wiki-to-graph.git

# source
git clone https://github.com/vanderbilt-ms-ai/wiki-to-graph.git
```

The PyPI package is at 0.2.0, behind this repository; publishing a new release (below) closes
that gap, after which `pip install wiki-to-graph` is equivalent.

## Publish a new release to PyPI

Packaging lives in [`pyproject.toml`](../pyproject.toml) (console entry points
`wiki-to-graph` and `wiki-to-graph-viewer`; stdlib-only, no runtime deps).

```bash
python3 -m pip install --upgrade build twine
python3 -m build                 # -> dist/*.tar.gz and dist/*.whl
python3 -m twine upload dist/*   # prompts for your PyPI token
```
Bump `version` in `pyproject.toml`, `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`
before each release.
To rehearse first: `twine upload --repository testpypi dist/*`.

## Directories & lists

- **Anthropic community plugin directory** — submit via the form at
  <https://clau.de/plugin-directory-submission> (PRs to the mirror repo are auto-closed).
- **claudemarketplaces.com** — community directory that indexes public Claude plugin repos.
- **Awesome lists** — e.g. `ComposioHQ/awesome-claude-plugins`, `ComposioHQ/awesome-claude-skills`.

## Announcement templates

Reusable copy for launch posts (Show HN, Reddit, Product Hunt) lives with the maintainers; keep
descriptions factual (state what it does, no sales pitch) and always note the license:
**CC BY-NC-SA 4.0 — free for personal/academic use; commercial use requires a paid license**
(contact tim.darrah@mangrove.ai).
