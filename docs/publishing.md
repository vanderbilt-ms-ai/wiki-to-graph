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
pip install wiki-to-graph

# source
git clone https://github.com/vanderbilt-ms-ai/wiki-to-graph.git
```

## Publish a new release

Packaging lives in [`pyproject.toml`](../pyproject.toml) (console entry points `wiki-to-graph` and
`wiki-to-graph-viewer`; modules `wiki_to_graph`, `wiki_normalize`, `build_graph_viewer`;
stdlib-only, no runtime dependencies). Release from an up-to-date `main`.

1. **Bump the version** in all four places: `pyproject.toml`, `.claude-plugin/plugin.json`,
   `.claude-plugin/marketplace.json` (metadata and plugin entry), and the `generator` string in
   `skills/wiki-to-graph/scripts/wiki_to_graph.py`. Merge that to `main`.
2. **Test:** `python3 -m unittest discover tests`.
3. **Build and check** (`build/lib/` and `dist/` are git-ignored):
   ```bash
   python3 -m pip install --upgrade build twine
   rm -rf dist && python3 -m build
   python3 -m twine check dist/*
   ```
4. **Upload** — prompts for a PyPI API token (username `__token__`). Rehearse with
   `--repository testpypi` if in doubt; a version number can never be re-uploaded.
   ```bash
   python3 -m twine upload dist/*
   ```
5. **Tag and release on GitHub**, attaching the same files:
   ```bash
   git tag -a vX.Y.Z -m "wiki-to-graph X.Y.Z" && git push origin vX.Y.Z
   gh release create vX.Y.Z dist/* --title "wiki-to-graph X.Y.Z" --notes-file <notes>
   ```

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
