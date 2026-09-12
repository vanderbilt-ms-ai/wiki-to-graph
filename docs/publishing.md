# Distribution & publishing

How to get `wiki-to-graph`, how to publish a new release, and where it's listed.

## Get it

**As a Claude plugin (Claude Code):**
```
/plugin marketplace add MangroveTechnologies/wiki-to-graph
/plugin install wiki-to-graph
```

**From PyPI:**
```bash
pip install wiki-to-graph
```
Installs two console commands: `wiki-to-graph` (the toolkit) and `wiki-to-graph-viewer`
(the HTML viewer generator).

**From source (no install):** the scripts are stdlib-only Python — clone and run them directly
(see the [README](../README.md) quick start).

## Publish a new release to PyPI

Packaging lives in [`pyproject.toml`](../pyproject.toml) (console entry points
`wiki-to-graph` and `wiki-to-graph-viewer`; stdlib-only, no runtime deps).

```bash
python3 -m pip install --upgrade build twine
python3 -m build                 # -> dist/*.tar.gz and dist/*.whl
python3 -m twine upload dist/*   # prompts for your PyPI token
```
Bump `version` in `pyproject.toml` (and `.claude-plugin/plugin.json`) before each release.
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
