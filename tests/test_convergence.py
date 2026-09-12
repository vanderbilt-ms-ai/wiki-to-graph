"""The build is format-invariant: the same content yields the same graph structure,
whatever shape the wiki was written in.

Run:  python3 -m unittest discover tests
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPTS = os.path.join(ROOT, "skills", "wiki-to-graph", "scripts")
EXAMPLE = os.path.join(ROOT, "examples", "llm-wiki", "wiki")
LEGACY = os.path.join(HERE, "fixtures", "legacy-vault")
sys.path.insert(0, SCRIPTS)
sys.path.insert(0, HERE)

import formats                                                     # noqa: E402
from wiki_normalize import (classify_type, hub_items, normalize_texts,  # noqa: E402
                            read_wiki, section_kind)

HUBS = ("index", "log")


def build(pages_or_dir):
    """Build through the real CLI (normalization included) and return graph.json."""
    with tempfile.TemporaryDirectory() as tmp:
        src = pages_or_dir
        if isinstance(pages_or_dir, dict):
            src = os.path.join(tmp, "wiki")
            os.makedirs(src)
            for fn, text in pages_or_dir.items():
                with open(os.path.join(src, fn), "w", encoding="utf-8") as fh:
                    fh.write(text)
        out = os.path.join(tmp, "graph.json")
        proc = subprocess.run([sys.executable, os.path.join(SCRIPTS, "wiki_to_graph.py"),
                               "build", src, "-o", out], capture_output=True, text=True)
        if proc.returncode:
            raise AssertionError("build failed:\n" + proc.stdout + proc.stderr)
        with open(out, encoding="utf-8") as fh:
            return json.load(fh)


def structure(graph, relations_only=False):
    """What must not depend on format: node identity and typing, and the typed edge set.
    Prose (summaries, reasons) may differ. Hub nodes and their navigation edges are
    excluded because a hub page is itself a formatting choice."""
    types = {n["id"]: n["type"] for n in graph["nodes"]}
    nodes = {(n["id"], n["type"], n.get("kind")) for n in graph["nodes"] if n["type"] not in HUBS}
    edges = set()
    for e in graph["links"]:
        if types.get(e["source"]) in HUBS or types.get(e["target"]) in HUBS:
            continue
        if relations_only and e["type"] == "mentions":
            continue
        ends = (tuple(sorted((e["source"], e["target"])))
                if e["type"] in ("related", "contradicts") else (e["source"], e["target"]))
        edges.add((e["type"],) + ends)
    return nodes, edges


class FormatInvariance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = read_wiki(EXAMPLE)
        cls.reference = structure(build(EXAMPLE))
        cls.reference_relations = structure(build(EXAMPLE), relations_only=True)

    def assertSameStructure(self, got, want):
        self.assertEqual(sorted(want[0] - got[0]), [], "nodes missing from the rendered build")
        self.assertEqual(sorted(got[0] - want[0]), [], "unexpected nodes in the rendered build")
        self.assertEqual(sorted(want[1] - got[1]), [], "edges missing from the rendered build")
        self.assertEqual(sorted(got[1] - want[1]), [], "unexpected edges in the rendered build")

    def test_reference_example_is_already_normal(self):
        normalized, _ = normalize_texts(self.pages)
        changed = sorted(fn for fn in self.pages if normalized.get(fn) != self.pages[fn])
        self.assertEqual(changed, [], "the bundled example should already be in the page contract")

    def test_reference_example_follows_the_contract(self):
        """Preconditions the renderings rely on, and what makes the example exemplary."""
        alias = {}
        for fn, text in self.pages.items():
            alias[fn[:-3].lower()] = fn
            m = re.search(r"^# (.+)$", text, re.M)
            alias[m.group(1).lower()] = fn
        sources = {fn: formats.split_frontmatter(t)[0].get("locator")
                   for fn, t in self.pages.items()
                   if formats.split_frontmatter(t)[0].get("type") == "source"}
        self.assertTrue(sources, "the example should include source pages")
        for fn, text in self.pages.items():
            fm, body = formats.split_frontmatter(text)
            if fn in ("index.md", "log.md"):
                continue
            head, secs = formats.split_sections(body)
            for name, content in secs:
                if name == "Related":
                    for b in formats.bullets(content):
                        m = formats.LEAD_RE.match(b)
                        self.assertTrue(m and m.group(2).strip(), "%s: related link without a reason: %s" % (fn, b))
                        self.assertNotIn("[[", m.group(2), "%s: a related reason should not link: %s" % (fn, b))
            if not formats.is_concept(fm):
                continue
            cited = {sources[f] for f in sources
                     if any(line.strip().startswith("- " + sources[f])
                            for name, c in secs if name == "Sources" for line in c.splitlines())}
            linked = {sources[alias[t.lower()]] for name, c in secs if name != "Sources"
                      for t, _a in formats.LINK_RE.findall(c) if alias.get(t.lower()) in sources}
            self.assertEqual(cited, linked, "%s: Sources should list exactly the source pages it links" % fn)

    def test_every_style_is_idempotent(self):
        for style, render in formats.STYLES.items():
            once, _ = normalize_texts(render(self.pages))
            twice, _ = normalize_texts(once)
            self.assertEqual(once, twice, "normalizing the %s style twice changed it" % style)

    def test_flat_style_builds_the_same_graph(self):
        self.assertSameStructure(structure(build(formats.render_flat(self.pages))), self.reference)

    def test_vault_style_builds_the_same_graph(self):
        self.assertSameStructure(structure(build(formats.render_vault(self.pages))), self.reference)

    def test_hub_style_builds_the_same_relations(self):
        # A hub moves disagreement prose onto one page, so the evidence those sentences
        # mention moves with it; every node and every typed relation must still match.
        got = structure(build(formats.render_hub(self.pages)), relations_only=True)
        self.assertSameStructure(got, self.reference_relations)


class LegacyWiki(unittest.TestCase):
    """The example as it shipped before the page contract: prose disagreements,
    'None across the sources' lines, citations joined on one line."""

    @classmethod
    def setUpClass(cls):
        cls.g = build(LEGACY)
        cls.nodes = {n["id"]: n for n in cls.g["nodes"]}

    def pairs(self, etype):
        return {tuple(sorted((e["source"], e["target"]))) for e in self.g["links"] if e["type"] == etype}

    def test_structurally_clean(self):
        w = self.g["meta"]["warnings"]
        self.assertEqual((w["dangling"], w["orphans"], w["self_loops"]), ([], [], []))

    def test_every_cited_paper_is_one_source_node(self):
        locs = sorted(n.get("locator") for n in self.g["nodes"] if n["type"] == "source")
        self.assertEqual(locs, ["raw/0%d_%s.md" % p for p in [
            (1, "attention_is_all_you_need"), (2, "bert"), (3, "gpt3"),
            (4, "foundation_models"), (5, "rlhf_instructgpt"), (6, "chinchilla")]])

    def test_citations_on_one_line_are_each_counted(self):
        cites = {e["target"] for e in self.nodes["autoregressive-language-model"]["edges"] if e["type"] == "cites"}
        self.assertEqual(len(cites), 2)

    def test_none_means_no_disagreement(self):
        for nid in ("transformer", "encoder-decoder-architecture", "reward-modeling"):
            self.assertFalse([e for e in self.g["links"] if e["type"] == "contradicts" and nid in (e["source"], e["target"])],
                             "%s says 'None' yet has a contradicts edge" % nid)

    def test_real_disagreements_survive(self):
        c = self.pairs("contradicts")
        for pair in [("bert", "gpt-3"), ("gpt-3", "rlhf"), ("chinchilla", "gpt-3")]:
            self.assertIn(pair, c)


class QueryByName(unittest.TestCase):
    """In conversation a page is named the way the wiki links it, often by its filename."""

    def test_query_resolves_a_filename_alias(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "graph.json")
            cli = [sys.executable, os.path.join(SCRIPTS, "wiki_to_graph.py")]
            subprocess.run(cli + ["build", EXAMPLE, "-o", out], check=True, capture_output=True)
            proc = subprocess.run(cli + ["query", out, "backlinks", "Hoffmann 2022", "--edges", "cites"],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("Chinchilla", proc.stdout)
            proc = subprocess.run(cli + ["analyze", out, "--top", "1", "--path", "Vaswani 2017", "RLHF"],
                                  capture_output=True, text=True)
            self.assertIn("not a concept page", proc.stdout)
            proc = subprocess.run(cli + ["analyze", out, "--top", "1", "--path", "Positional Encoding", "RLHF"],
                                  capture_output=True, text=True)
            self.assertIn("Positional Encoding \u2192", proc.stdout)


class Parsing(unittest.TestCase):
    def test_section_synonyms(self):
        self.assertEqual(section_kind("See also"), "related")
        self.assertEqual(section_kind("Tensions"), "contradicts")
        self.assertEqual(section_kind("Contradictions / tensions"), "contradicts")
        self.assertEqual(section_kind("References"), "cites")
        self.assertIsNone(section_kind("The case against"))

    def test_type_line_vocabulary(self):
        self.assertEqual(classify_type("paper · **File:** `raw/x.pdf`"), ("source", "paper"))
        self.assertEqual(classify_type("training objective"), ("concept", "procedure"))
        self.assertEqual(classify_type("failure mode"), ("concept", "fact"))
        self.assertEqual(classify_type("model class"), ("concept", "schema"))
        self.assertEqual(classify_type("technique · **contested**"), ("concept", "procedure"))

    def test_hub_bullet_shapes(self):
        text = "\n".join([
            "# Contradictions", "## Direct reversals",
            "### 1. Scale is the driver / alignment is",
            "- [[brown]], [[devlin]]: capability tracks size.",
            "- [[ouyang]]: a 1.3B aligned model wins.",
            "See [[scale]].",
            "### 2. Longer is better / waste",
            "- Complexity-based prompting, in [[schulhoff]]: longer is better.",
            "- [[alomrani]] and [[wei]] find length is waste.",
            "### 3. Only prose", "[[a]] argues one thing and [[b]] another."])
        items = hub_items(text)
        self.assertEqual(items[0][1], [(["brown", "devlin"], "capability tracks size."),
                                       (["ouyang"], "a 1.3B aligned model wins.")])
        self.assertEqual(items[0][2], ["scale"])
        self.assertEqual([s for s, _ in items[1][1]], [["schulhoff"], ["alomrani", "wei"]])
        self.assertEqual(items[2][1], [])


if __name__ == "__main__":
    unittest.main()
