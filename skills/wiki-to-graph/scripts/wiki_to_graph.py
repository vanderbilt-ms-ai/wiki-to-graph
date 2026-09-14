#!/usr/bin/env python3
"""
wiki_to_graph — translate an LLM wiki (folder of markdown entity pages) into a
typed property graph traversable by graph algorithms.

Ontology (see references/spec.md):
  nodes: concept (entity page), source (doc/citation in ## Sources)
  edges: mentions (body links), related (## Related), contradicts (## Contradictions),
         cites (concept -> source)

Canonical output: graph.json (node-link, NetworkX-compatible).
Optional: --emit sqlite,graphml  and  --kst (domain.json for the KST toolkit).

Stdlib only. Usage:
  python3 wiki_to_graph.py <wiki_dir> [-o graph.json] [--emit sqlite,graphml]
                            [--stubs] [--dag-edges mentions] [--kst] [--exclude index,log]
"""
import argparse, glob, json, os, re, shutil, sqlite3, sys, tempfile, datetime, xml.sax.saxutils as sx

# Locators, the section vocabulary and structural normalization live in one module so
# the parser and the normalizer can never disagree about what a heading or locator means.
from wiki_normalize import (LOCATOR_RE, locator_in, medium_for, section_kind,
                            normalize_wiki, report_lines)

LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
CODE_RE = re.compile(r"`[^`]*`")
H1_RE   = re.compile(r"^#\s+(.*)$")
H2_RE   = re.compile(r"^##\s+(.*)$")

DEFAULT_MAP = [  # (predicate on lowercased section name, edge type)
    # Synonyms are accepted ("See also", "Tensions", "References", ...) because a wiki is
    # rarely written with this parser in mind; see wiki_normalize.section_kind.
    (lambda s: section_kind(s) == "contradicts", "contradicts"),
    (lambda s: section_kind(s) == "related",     "related"),
    (lambda s: section_kind(s) == "cites",       "cites"),
    (lambda s: True,                             "mentions"),  # summary/explanation/other
]
SYMMETRIC = {"related", "contradicts"}
# index.md / log.md are navigational hubs, not concepts. Their links get their own
# edge types so they don't pollute concept-level semantics (e.g. a "tensions" section
# heading in index.md must NOT be read as a `contradicts` edge).
META_EDGE = {"index": "indexes", "log": "records"}
CONCEPT_EDGE_TYPES = {"mentions", "related", "contradicts", "cites"}


NODE_TYPES = {"concept", "source", "index", "log"}

def node_type_for(stem, meta=None):
    """Declared `type:` in frontmatter wins; filename stem is the legacy fallback."""
    declared = (meta or {}).get("type", "").strip().lower()
    if declared in NODE_TYPES:
        return declared
    s = stem.lower()
    if s == "index":
        return "index"
    if s == "log":
        return "log"
    return "concept"


def slug(text):
    s = re.sub(r"[^a-z0-9]+", "-", text.strip().lower()).strip("-")
    return s or "untitled"


def strip_links(text):
    """Replace [[Target|alias]] / [[Target]] with plain text. The relationship is
    encoded as a structured edge instead of being reproduced as markup in the prose."""
    return LINK_RE.sub(lambda m: (m.group(2) or m.group(1)).strip(), text)


YEAR_RE = re.compile(r"(?<!\d)(1[5-9]\d\d|20\d\d|21\d\d)(?!\d)")
CITED_YEAR_RE = re.compile(r"\(([^()]*)\)\s*$")


def year_of(meta, title="", stem=""):
    """-> (year, basis), or (None, None).

    A declared `date:` (or `year:`) wins. For a source, a title ending in a citation,
    "Attention Is All You Need (Vaswani et al., 2017)", or a filename such as
    vaswani-2017-attention is the fallback. A year anywhere else in a title is not
    trusted: in "2024-T3 plate", 2024 is an aluminium alloy, not a date."""
    d = YEAR_RE.search(str(meta.get("date") or meta.get("year") or ""))
    if d:
        return int(d.group(1)), "date"
    m = CITED_YEAR_RE.search(title or "")
    years = YEAR_RE.findall(m.group(1)) if m else []
    if years:
        return int(years[-1]), "title"
    m = re.search(r"(?:^|[-_ ])(1[5-9]\d\d|20\d\d|21\d\d)(?=[-_ ]|$)", stem or "")
    if m:
        return int(m.group(1)), "filename"
    return None, None


def parse_topics(value):
    """`topics: Field / Topic, Other` or `[a, b]` -> ["Field / Topic", "Other"].

    A topic is a coarse grouping of pages (a field, a subject area), not an atom of
    knowledge: atoms are concept pages. "Field / Topic" nests a topic under a field so
    a filter can select either level."""
    out = []
    for t in re.split(r"[,;]", (value or "").strip().strip("[]")):
        t = re.sub(r"\s*/\s*", " / ", t.strip().strip("\"'"))
        if t and t not in out:
            out.append(t)
    return out


def topic_matches(topics, wanted):
    """True if any topic equals a wanted name or sits under it ("Field" matches "Field / X")."""
    low = [t.lower() for t in topics or []]
    return any(t == w or t.startswith(w + " / ") for t in low for w in wanted)


# knowledge-node taxonomy (the `kind` property). Structural `type` stays concept/
# source/index/log; `kind` classifies the knowledge a concept node holds.
#
# These five names are this tool's DEFAULT vocabulary, not a fixed one. A wiki built on a different
# ontology (more primitives, different relation names) can supply its own with `--vocab v.json`;
# see load_vocab(). Everything downstream reads these module globals, so overriding them is the
# single switch — but that only works if you override ALL of them, which is what --vocab is for:
# leaving CONCEPT_EDGE_TYPES on the defaults while using custom section names produces a graph
# that builds cleanly and reports every node as an orphan, because degree is computed over edge
# types that no longer exist.
KINDS = {"concept", "fact", "schema", "procedure"}


DEFAULT_VOCAB = {
    "kinds": sorted(KINDS),
    "concept_edges": sorted(CONCEPT_EDGE_TYPES),
    "symmetric": sorted(SYMMETRIC),
    "hub_edges": sorted(META_EDGE.values()),
}


def load_vocab(path):
    """Replace the built-in kind/edge vocabulary from a JSON file.

    Shape (every key optional; omitted keys keep the default):

        {"kinds":         ["object", "concept", "fact", "experience", …],
         "concept_edges": ["part-of", "uses", "derived-from", …],
         "symmetric":     ["contradicts", "co-occurred-with"],
         "hub_edges":     ["indexes", "records"]}

    `concept_edges` is the one people miss. It drives in/out degree at build time AND the analysis
    graph, so a custom section->edge map without a matching vocabulary yields a graph where every
    node looks like an orphan and `analyze` considers zero edges.
    """
    global KINDS, CONCEPT_EDGE_TYPES, CONCEPT_EDGE, ALL_EDGE_TYPES, SYMMETRIC
    v = dict(DEFAULT_VOCAB)
    if path:
        with open(path, encoding="utf-8") as fh:
            v.update(json.load(fh))
    KINDS = set(v["kinds"])
    CONCEPT_EDGE_TYPES = set(v["concept_edges"])
    CONCEPT_EDGE = set(v["concept_edges"])
    SYMMETRIC = set(v["symmetric"])
    ALL_EDGE_TYPES = list(v["concept_edges"]) + list(v["hub_edges"])
    return v


def edge_type_for(section, mapping):
    s = section.strip().lower()
    for pred, et in mapping:
        if pred(s):
            return et
    return "mentions"


def parse_page(path):
    """Return (title, {section_name: [lines]}, meta). meta carries any simple
    `key: value` pairs from optional YAML-ish frontmatter (--- ... ---), notably
    `kind`, `type`, `medium`, `locator`, `author`, `date`."""
    title, sections, cur, meta = None, {}, None, {}
    lines = open(path, encoding="utf-8").read().split("\n")
    i = 0
    if lines and lines[0].strip() == "---":            # optional frontmatter
        j = 1
        while j < len(lines) and lines[j].strip() != "---":
            m = re.match(r"\s*([A-Za-z_][\w-]*)\s*:\s*(.*?)\s*$", lines[j])
            if m:
                k, v = m.group(1).strip().lower(), m.group(2).strip().strip('"\'')
                if v:
                    meta[k] = v.lower() if k in ("kind", "type", "medium") else v
            j += 1
        i = j + 1
    fence = False
    for raw in lines[i:]:
        line = raw.rstrip("\n")
        if line.lstrip().startswith("```"):
            fence = not fence            # a '# comment' inside a code block is not a heading
            if cur is not None:
                sections[cur].append(line)
            continue
        m1 = None if fence else H1_RE.match(line)
        m2 = None if fence else H2_RE.match(line)
        if m1 and title is None:
            title = m1.group(1).strip()
        elif m2:
            cur = m2.group(1).strip()
            sections.setdefault(cur, [])
        elif cur is not None:
            sections[cur].append(line)
    if title is None:
        title = os.path.splitext(os.path.basename(path))[0]
    return title, sections, meta


BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
MAX_CONTEXT = 400


def blocks_of(text):
    """Split section text into logical blocks — each list item (with its wrapped
    continuation lines) and each paragraph. The block a link sits in is where the
    author wrote WHY the link is there, so it is the link's context."""
    blocks, cur = [], []
    for raw in text.split("\n"):
        if not raw.strip():
            if cur:
                blocks.append("\n".join(cur)); cur = []
            continue
        if BULLET_RE.match(raw) and cur:
            blocks.append("\n".join(cur)); cur = [raw]
        else:
            cur.append(raw)
    if cur:
        blocks.append("\n".join(cur))
    return blocks


NONE_RE = re.compile(
    r"^\W*(none|no (?:known |real )?(?:contradictions?|tensions?|conflicts?|disagreements?)|n/?a)\b",
    re.I)


def link_contexts(text, subject_rule=False):
    """-> {target: {"count", "context", "typed"}}.

    `context` is the prose of the bullet or paragraph the link sits in \u2014 where the
    author said WHY the link is there. A leading "[[X]] \u2014 " is the bullet's subject
    and already the edge's target, so it is left out; a block that is only links
    ("[[a]] \u00b7 [[b]]") has no prose, so its edges get "" rather than sibling names.

    `typed` says whether the link carries the section's relation or is only mentioned.
    A bare link list types every link. Otherwise a block states one relation, and
    links cited inside its prose are evidence:

      "- [[A]] \u2014 because [[P]] found X"      A is the relation, P a mention

    With `subject_rule` (disagreement sections) every prose block names exactly one
    subject even without a leading link, because disagreements are overwhelmingly
    written as sentences citing evidence:
      a leading link           "- [[A]]: claim"
      else a link in a label   "- **vs [[A]]:** ..."
      else the first link      "[[A]] contrasts with the objective of [[B]]"
      none at all              "None across the sources \u2014 see [[A]] and [[B]]"
    Typing every link in such a sentence asserts disagreements it never makes.
    """
    out = {}
    for block in blocks_of(CODE_RE.sub("", text)):
        found = LINK_RE.findall(block)
        if not found:
            continue
        is_bullet = bool(BULLET_RE.match(block))
        body = BULLET_RE.sub("", block.strip())
        lead_m = re.match(r"\s*\[\[([^\]|]+)(?:\|[^\]]*)?\]\]\s*[\u2014\u2013:-]\s+", body)
        rest = body[lead_m.end():] if lead_m else body
        bare = re.sub(r"[\s\u00b7*+:;,.|\u2014\u2013-]+", " ", LINK_RE.sub("", rest)).strip()
        has_prose = len(bare) >= 12
        ctx = ""
        if has_prose:
            ctx = re.sub(r"\s+", " ", strip_links(rest)).strip()
            if len(ctx) > MAX_CONTEXT:
                ctx = ctx[:MAX_CONTEXT].rsplit(" ", 1)[0] + "\u2026"
        if not has_prose:
            subject, typed_all = None, True
        elif subject_rule:
            typed_all = False
            if NONE_RE.match(strip_links(body)):
                subject = None
            elif lead_m:
                subject = lead_m.group(1).strip()
            else:
                label = re.match(r"\s*\*\*(.+?)\*\*", body)
                in_label = LINK_RE.findall(label.group(1)) if label else []
                subject = (in_label[0][0] if in_label else found[0][0]).strip()
        else:
            subject = lead_m.group(1).strip() if (is_bullet and lead_m) else None
            typed_all = subject is None
        for t, _alias in found:
            t = t.strip()
            if not t or t.lower() == "wiki-links":
                continue
            e = out.setdefault(t, {"count": 0, "context": "", "typed": False})
            e["count"] += 1
            if typed_all or t == subject:
                e["typed"] = True
            if len(ctx) > len(e["context"]):
                e["context"] = ctx
    return out


def links_in(text):
    """Yield (target, count) from text, ignoring inline-code spans."""
    clean = CODE_RE.sub("", text)
    out = {}
    for t, _alias in LINK_RE.findall(clean):
        t = t.strip()
        if t and t.lower() != "wiki-links":  # illustrative token
            out[t] = out.get(t, 0) + 1
    return out


def build_graph(wiki_dir, exclude, mapping, stubs):
    files = sorted(glob.glob(os.path.join(wiki_dir, "*.md")))
    files = [f for f in files
             if os.path.splitext(os.path.basename(f))[0].lower() not in exclude]

    # pass 1: nodes + alias table
    pages, alias = {}, {}
    for f in files:
        title, sections, meta = parse_page(f)
        stem = os.path.splitext(os.path.basename(f))[0]
        ntype = node_type_for(stem, meta)
        cid = slug(title)
        # `kind` classifies KNOWLEDGE, so it applies only to concept nodes. A source
        # is an artifact, not an atom of knowledge — it CONTAINS facts, it is not one.
        kind = (meta.get("kind") if meta.get("kind") in KINDS else "concept") \
            if ntype == "concept" else None
        pages[cid] = {"file": os.path.basename(f), "title": title, "meta": meta,
                      "sections": sections, "ntype": ntype, "kind": kind}
        alias[title.lower()] = cid
        alias[stem.lower()] = cid

    nodes, edges = {}, []
    warnings = {"dangling": [], "orphans": [], "self_loops": [], "dup_ids": []}
    seen_ids = {}
    src_nodes = {}

    # locator -> id of an AUTHORED source page, so `## Sources` bullets attach to a
    # real page when one exists instead of minting a parallel stub for the same artifact.
    loc_index = {}
    for _cid, _p in pages.items():
        if _p["ntype"] == "source":
            _loc = (_p["meta"].get("locator") or "").strip().lower()
            if _loc:
                loc_index[_loc] = _cid

    def resolve_source(bullet):
        """A `## Sources` bullet -> node id. Prefers an authored source page
        (by [[link]] or by declared locator); falls back to a generated stub."""
        for _t, _a in LINK_RE.findall(CODE_RE.sub("", bullet)):
            tid = alias.get(_t.strip().lower())
            if tid and pages.get(tid, {}).get("ntype") == "source":
                return tid
        loc = locator_in(bullet)
        if loc and loc.strip().lower() in loc_index:
            return loc_index[loc.strip().lower()]
        key = loc or re.split(r"[ (]", bullet)[0][:60]
        sid = "src:" + slug(key)
        if sid not in src_nodes:
            src_nodes[sid] = {"id": sid, "type": "source", "kind": None,
                              "ref": bullet, "title": bullet,
                              "locator": loc, "path": loc, "medium": medium_for(loc),
                              "in_degree": 0, "out_degree": 0, "edges": []}
            yr, basis = year_of({}, bullet)
            if yr:
                src_nodes[sid].update(year=yr, year_basis=basis)
        return sid

    def add_edge(s, t, et, via, w=1, context=""):
        directed = et not in SYMMETRIC
        for e in edges:
            if e["source"] == s and e["target"] == t and e["type"] == et:
                e["weight"] += w
                if len(context) > len(e.get("context") or ""):
                    e["context"] = context      # keep the most explanatory mention
                return
        edges.append({"source": s, "target": t, "type": et, "via": via,
                      "directed": directed, "weight": w, "context": context})

    for cid, p in pages.items():
        if cid in seen_ids:
            warnings["dup_ids"].append([cid, p["file"], seen_ids[cid]])
        seen_ids[cid] = p["file"]

        # index / log: navigational hub nodes. Every link becomes an `indexes` /
        # `records` edge, regardless of which section it sits in.
        if p["ntype"] in META_EDGE:
            met = META_EDGE[p["ntype"]]
            nodes[cid] = {"id": cid, "type": p["ntype"], "kind": None, "title": p["title"],
                          "summary": "", "explanation": "", "sources": [],
                          "file": p["file"], "in_degree": 0, "out_degree": 0, "edges": []}
            for sec, lines in p["sections"].items():
                for tgt, info in link_contexts("\n".join(lines)).items():
                    tid = alias.get(tgt.lower())
                    if tid is None:
                        warnings["dangling"].append([p["title"], tgt])
                        continue
                    if tid != cid:
                        add_edge(cid, tid, met, sec, info["count"], info["context"])
            continue

        # link markup is stripped to plain text — the relationship is encoded as an
        # edge (below), not reproduced as [[markup]] in the prose.
        # `## Summary` / `## Explanation` are a convention, not a guarantee: pages
        # derived from a web page, a deck or a transcript often use their own headings.
        # Fall back to the substantive (mentions-typed) sections so no node is blank.
        prose = [(sec, strip_links("\n".join(ln).strip()))
                 for sec, ln in p["sections"].items()
                 if edge_type_for(sec, mapping) == "mentions"]
        prose = [(sec, t) for sec, t in prose if t]
        named = dict(prose)
        summary = named.get("Summary", "")
        expl = named.get("Explanation", "")
        if not summary:
            rest = [(sec, t) for sec, t in prose if sec != "Explanation"]
            if rest:
                summary = rest[0][1][:400]
                used = rest[0][0]
            else:
                used = None
        else:
            used = "Summary"
        if not expl:
            expl = "\n\n".join(t for sec, t in prose if sec not in (used, "Summary"))
        source_strings = []
        node = {"id": cid, "type": p["ntype"], "kind": p["kind"], "title": p["title"],
                "summary": summary, "explanation": expl,
                "sources": source_strings, "file": p["file"],
                "in_degree": 0, "out_degree": 0, "edges": []}
        if p["ntype"] == "source":
            loc = p["meta"].get("locator")
            node["locator"] = loc
            node["path"] = loc                       # back-compat alias
            node["medium"] = p["meta"].get("medium") or medium_for(loc)
            for _k in ("author", "date", "publisher", "accessed"):
                if p["meta"].get(_k):
                    node[_k] = p["meta"][_k]
        is_src = p["ntype"] == "source"
        yr, basis = year_of(p["meta"], p["title"] if is_src else "",
                            os.path.splitext(p["file"])[0] if is_src else "")
        if yr:
            node["year"], node["year_basis"] = yr, basis
        topics = parse_topics(p["meta"].get("topics") or p["meta"].get("topic"))
        if topics:
            node["topics"] = topics
        nodes[cid] = node

        for sec, lines in p["sections"].items():
            et = edge_type_for(sec, mapping)
            text = "\n".join(lines)
            if et == "cites":
                for ln in lines:
                    b = ln.strip().lstrip("-*").strip()
                    if not b:
                        continue
                    # "raw/a.md (X); raw/b.md (Y)" on one line is two citations, not one
                    parts = ([x.strip() for x in b.split(";")]
                             if len(LOCATOR_RE.findall(b)) > 1 else [b])
                    for part in parts:
                        if not part:
                            continue
                        source_strings.append(part)
                        sid = resolve_source(part)
                        if sid != cid:
                            add_edge(cid, sid, "cites", sec, 1,
                                     re.sub(r"\s+", " ", strip_links(part)).strip())
                continue
            for tgt, info in link_contexts(text, subject_rule=(et == "contradicts")).items():
                cnt = info["count"]
                # In a typed-relation section, only what a bullet is ABOUT carries the
                # relation. Links cited inside the bullet's prose are evidence, and
                # typing them as `contradicts`/`related` asserts a disagreement or
                # association the sentence never claimed. Prose blocks keep the section
                # type for every link, which is the older paragraph-style convention.
                etype = et if info["typed"] else "mentions"
                tid = alias.get(tgt.lower())
                if tid is None:
                    warnings["dangling"].append([p["title"], tgt])
                    if stubs:
                        tid = slug(tgt)
                        nodes.setdefault(tid, {"id": tid, "type": "missing",
                                               "title": tgt, "summary": "", "explanation": "",
                                               "sources": [], "file": None,
                                               "in_degree": 0, "out_degree": 0})
                    else:
                        continue
                if tid == cid:
                    warnings["self_loops"].append([cid, sec])
                    continue
                add_edge(cid, tid, etype, sec, cnt, info["context"])

    nodes.update(src_nodes)

    # degree_by_type: full breakdown; in_degree/out_degree are the SEMANTIC totals
    # (hub edges indexes/records excluded, so the index doesn't inflate every node).
    HUB = {"indexes", "records"}
    for n in nodes.values():
        n["degree_by_type"] = {"in": {}, "out": {}}
    for e in edges:
        t = e["type"]
        s, d = nodes.get(e["source"]), nodes.get(e["target"])
        if s: s["degree_by_type"]["out"][t] = s["degree_by_type"]["out"].get(t, 0) + 1
        if d: d["degree_by_type"]["in"][t] = d["degree_by_type"]["in"].get(t, 0) + 1
    for n in nodes.values():
        n["out_degree"] = sum(v for t, v in n["degree_by_type"]["out"].items() if t not in HUB)
        n["in_degree"]  = sum(v for t, v in n["degree_by_type"]["in"].items()  if t not in HUB)
    # orphan = a concept with no *concept-level* edges. Hub edges from index/log
    # (`indexes`/`records`) don't count, or nothing would ever be an orphan.
    cdeg = {nid: 0 for nid in nodes}
    for e in edges:
        if e["type"] in CONCEPT_EDGE_TYPES:
            if e["source"] in cdeg:
                cdeg[e["source"]] += 1
            if e["target"] in cdeg:
                cdeg[e["target"]] += 1
    for nid, n in nodes.items():
        if n["type"] == "concept" and cdeg[nid] == 0:
            warnings["orphans"].append(nid)

    # A concept rarely states a year or topic, but the sources it cites do. It inherits the
    # topic(s) most of its sources share (ties kept), not their union, which would tag a
    # page citing five papers with every topic any of them touches. It takes the earliest
    # of their years: when this collection first records the idea. Both say they were
    # derived, so a reader can tell an authored value from an inherited one.
    cited = {}
    for e in edges:
        if e["type"] == "cites":
            cited.setdefault(e["source"], []).append(e["target"])
    for nid, n in nodes.items():
        if n["type"] != "concept":
            continue
        srcs = [nodes.get(s) or src_nodes.get(s) for s in cited.get(nid, [])]
        srcs = [s for s in srcs if s]
        if not n.get("topics"):
            tally = {}
            for s in srcs:
                for t in s.get("topics", []):
                    tally[t] = tally.get(t, 0) + 1
            if tally:
                top = max(tally.values())
                n["topics"] = sorted(t for t, c in tally.items() if c == top)
                n["topics_basis"] = "cited sources"
        years = [s["year"] for s in srcs if s.get("year")]
        if years and not n.get("year"):
            n["year"], n["year_basis"] = min(years), "earliest cited source"

    # extra per-node metadata
    for n in nodes.values():
        if n["type"] in ("concept", "source"):
            n["n_sources"] = len(n.get("sources", []))
            n["word_count"] = len((n.get("summary", "") + " " + n.get("explanation", "")).split())
            stem = os.path.splitext(n["file"])[0] if n.get("file") else n["title"]
            n["aliases"] = sorted({n["title"], stem})

    # Attach each node's outgoing edges directly ON the node (adjacency list).
    # This is the canonical carrier: edges live in the graph as structured typed
    # relations, not as [[markup]] reproduced inside the prose.
    for e in edges:
        if e["source"] in nodes:
            nodes[e["source"]]["edges"].append(
                {"target": e["target"], "type": e["type"], "via": e["via"],
                 "weight": e["weight"], "context": e.get("context", "")})

    return nodes, edges, warnings


def dag_report(nodes, edges, dag_edges):
    """Tarjan SCC over the chosen edge subset; report acyclicity."""
    adj = {n: [] for n in nodes}
    for e in edges:
        if e["type"] in dag_edges and e["source"] in adj:
            adj[e["source"]].append(e["target"])
    index, stack, on, idx, low, sccs = {}, [], set(), [0], {}, []
    def strong(v):
        idx[v] = low[v] = index[v] = index.get(v, len(index))
        index[v] = len(index) if v not in index else index[v]
    # iterative Tarjan
    counter = [0]; idxs = {}; lowl = {}; onstack = set(); st = []; out = []
    def dfs(v):
        idxs[v] = lowl[v] = counter[0]; counter[0]+=1; st.append(v); onstack.add(v)
        for w in adj.get(v, []):
            if w not in idxs:
                dfs(w); lowl[v]=min(lowl[v],lowl[w])
            elif w in onstack:
                lowl[v]=min(lowl[v],idxs[w])
        if lowl[v]==idxs[v]:
            comp=[]
            while True:
                w=st.pop(); onstack.discard(w); comp.append(w)
                if w==v: break
            out.append(comp)
    sys.setrecursionlimit(10000)
    for v in list(adj):
        if v not in idxs:
            dfs(v)
    cycles=[c for c in out if len(c)>1]
    return {"edge_types": sorted(dag_edges), "acyclic": not cycles,
            "cyclic_components": cycles}


def write_graphml(nodes, edges, path):
    def esc(x): return sx.escape(str(x)) if x is not None else ""
    keys = [("d_type","type","node","string"),("d_kind","kind","node","string"),
            ("d_title","title","node","string"),("d_year","year","node","int"),
            ("d_topics","topics","node","string"),
            ("e_type","type","edge","string"),("e_via","via","edge","string"),
            ("e_w","weight","edge","int")]
    with open(path,"w",encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        fh.write('<graphml xmlns="http://graphml.graphdrawing.org/xmlns">\n')
        for kid,name,dom,typ in keys:
            fh.write(f'<key id="{kid}" for="{dom}" attr.name="{name}" attr.type="{typ}"/>\n')
        fh.write('<graph edgedefault="directed">\n')
        for nid,n in nodes.items():
            fh.write(f'<node id="{esc(nid)}"><data key="d_type">{esc(n["type"])}</data>'
                     f'<data key="d_kind">{esc(n.get("kind"))}</data>'
                     f'<data key="d_title">{esc(n.get("title"))}</data>'
                     + (f'<data key="d_year">{n["year"]}</data>' if n.get("year") else '')
                     + (f'<data key="d_topics">{esc("; ".join(n["topics"]))}</data>' if n.get("topics") else '')
                     + '</node>\n')
        for i,e in enumerate(edges):
            fh.write(f'<edge id="e{i}" source="{esc(e["source"])}" target="{esc(e["target"])}">'
                     f'<data key="e_type">{esc(e["type"])}</data>'
                     f'<data key="e_via">{esc(e["via"])}</data>'
                     f'<data key="e_w">{e["weight"]}</data></edge>\n')
        fh.write('</graph>\n</graphml>\n')


def write_sqlite(nodes, edges, path):
    # Some mounted/network filesystems don't support SQLite's locking + rollback
    # journal (raising "disk I/O error"). Build in a local temp dir, then copy the
    # finished single-file DB to the destination (a plain file copy always works).
    import tempfile, shutil
    tmp = os.path.join(tempfile.mkdtemp(), "graph.db")
    con=sqlite3.connect(tmp); c=con.cursor()
    c.execute("""CREATE TABLE nodes(id TEXT PRIMARY KEY,type TEXT,kind TEXT,title TEXT,summary TEXT,
                 explanation TEXT,sources TEXT,file TEXT,word_count INT,n_sources INT,
                 in_degree INT,out_degree INT,year INT,topics TEXT)""")
    c.execute("""CREATE TABLE edges(src TEXT,dst TEXT,type TEXT,via TEXT,directed INT,weight INT)""")
    for n in nodes.values():
        c.execute("INSERT INTO nodes VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  (n["id"],n["type"],n.get("kind"),n.get("title"),n.get("summary",""),
                   n.get("explanation",""),json.dumps(n.get("sources",[])),n.get("file"),
                   n.get("word_count",0),n.get("n_sources",0),
                   n.get("in_degree",0),n.get("out_degree",0),
                   n.get("year"),json.dumps(n.get("topics",[]))))
    for e in edges:
        c.execute("INSERT INTO edges VALUES(?,?,?,?,?,?)",
                  (e["source"],e["target"],e["type"],e["via"],int(e["directed"]),e["weight"]))
    con.commit(); con.close()
    shutil.copyfile(tmp, path)


def write_kst(nodes, edges, path, dag_edges):
    items=[{"id":n["id"],"name":n["title"],"description":n.get("summary","")}
           for n in nodes.values() if n["type"]=="concept"]
    prereqs=[[e["target"],e["source"]] for e in edges if e["type"] in dag_edges]
    doc={"course":"(derived from wiki)","version":"0.1-candidate",
         "note":"prerequisites are HEURISTIC candidates from body references; curate before use.",
         "items":items,"prerequisites":sorted(prereqs)}
    open(path,"w",encoding="utf-8").write(json.dumps(doc,indent=2,ensure_ascii=False))


def cmd_build(args):
    exclude={x.strip().lower() for x in args.exclude.split(",") if x.strip()}
    mapping=DEFAULT_MAP
    if args.map:
        raw=json.load(open(args.map))
        mapping=[( (lambda kw: (lambda s: kw in s))(k), v) for k,v in raw.items()]
        mapping.append((lambda s: True,"mentions"))

    # Normalize a COPY first, so a wiki in any common shape builds the same graph as
    # the same content in the page contract. The source wiki is never modified.
    work, tmp, norm = args.wiki_dir, None, None
    if not args.no_normalize:
        if args.emit_normalized:
            work = args.emit_normalized
        else:
            tmp = work = tempfile.mkdtemp(prefix="wiki-normalized-")
        try:
            norm = normalize_wiki(args.wiki_dir, work)
        except ValueError as ex:
            print(ex); sys.exit(1)
    try:
        nodes,edges,warnings=build_graph(work,exclude,mapping,args.stubs)
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)

    ecount={}
    for e in edges: ecount[e["type"]]=ecount.get(e["type"],0)+1
    ncount={}
    for n in nodes.values(): ncount[n["type"]]=ncount.get(n["type"],0)+1
    dag=dag_report(nodes,edges,{x.strip() for x in args.dag_edges.split(",") if x.strip()})
    topic_counts={}
    for n in nodes.values():
        for t in n.get("topics") or []:
            topic_counts[t]=topic_counts.get(t,0)+1
    years=sorted(n["year"] for n in nodes.values() if n.get("year"))
    year_span={"min":years[0],"max":years[-1]} if years else None

    # multigraph=True: two nodes may be joined by several *typed* edges
    # (e.g. both `related` and `mentions`); a simple DiGraph would collapse them.
    graph={"directed":True,"multigraph":True,
           "meta":{"generator":"wiki_to_graph/1.0",
                   "generated":datetime.datetime.now().isoformat(timespec="seconds"),
                   "source_dir":os.path.normpath(args.wiki_dir),
                   "counts":{**ncount,"edges":ecount},
                   "dag_check":dag,"warnings":warnings,"normalization":norm,
                   "topics":dict(sorted(topic_counts.items())),"years":year_span},
           "nodes":list(nodes.values()),
           "links":edges}
    open(args.out,"w",encoding="utf-8").write(json.dumps(graph,indent=2,ensure_ascii=False))

    base=os.path.splitext(args.out)[0]
    emits={x.strip().lower() for x in args.emit.split(",") if x.strip()}
    if "sqlite" in emits: write_sqlite(nodes,edges,base+".db")
    if "graphml" in emits: write_graphml(nodes,edges,base+".graphml")
    if args.kst: write_kst(nodes,edges,base.replace("graph","domain")+".json",
                                 {x.strip() for x in args.dag_edges.split(",")})

    print(f"nodes: {ncount}  edges: {ecount}")
    print(f"dangling links: {len(warnings['dangling'])}  orphans: {len(warnings['orphans'])}  "
          f"self-loops: {len(warnings['self_loops'])}")
    print(f"DAG check over {dag['edge_types']}: "
          f"{'acyclic' if dag['acyclic'] else 'CYCLES: '+str(dag['cyclic_components'])}")
    if topic_counts or year_span:
        print(f"topics: {len(topic_counts)}  years: "
              + (f"{year_span['min']}–{year_span['max']}" if year_span else "none"))
    if norm is not None:
        done = report_lines(norm)
        print("normalized: " + ("; ".join(done) if done else "already in the page contract, nothing changed"))
    print(f"wrote {args.out}" + (f" (+ {', '.join(sorted(emits))})" if emits else ""))


# ---------------------------------------------------------------------------
# analysis (stdlib only — no numpy/scipy/networkx needed)
# ---------------------------------------------------------------------------
CONCEPT_EDGE = {"mentions", "related", "contradicts", "cites"}


def load_graph(path):
    g = json.load(open(path, encoding="utf-8"))
    nodes = {n["id"]: n for n in g["nodes"]}
    return g, nodes, g.get("links", [])


def _adj(node_ids, edges, types, undirected=False):
    a = {n: set() for n in node_ids}
    for e in edges:
        if e["type"] in types and e["source"] in a and e["target"] in a:
            a[e["source"]].add(e["target"])
            if undirected:
                a[e["target"]].add(e["source"])
    return a


def pagerank(node_ids, adj, d=0.85, it=200, tol=1e-10):
    N = len(node_ids)
    if not N:
        return {}
    pr = {n: 1.0 / N for n in node_ids}
    out = {n: len(adj.get(n, ())) for n in node_ids}
    for _ in range(it):
        dangling = d * sum(pr[n] for n in node_ids if out[n] == 0) / N
        new = {n: (1 - d) / N + dangling for n in node_ids}
        for n in node_ids:
            if out[n]:
                share = d * pr[n] / out[n]
                for m in adj[n]:
                    new[m] += share
        if sum(abs(new[n] - pr[n]) for n in node_ids) < tol:
            pr = new
            break
        pr = new
    return pr


def weak_components(node_ids, adjU):
    seen, comps = set(), []
    for s in node_ids:
        if s in seen:
            continue
        stack, comp = [s], []
        while stack:
            v = stack.pop()
            if v in seen:
                continue
            seen.add(v); comp.append(v)
            stack.extend(adjU.get(v, ()))
        comps.append(comp)
    return sorted(comps, key=len, reverse=True)


def label_propagation(node_ids, adjU, rounds=50):
    import random
    random.seed(42)
    label = {n: n for n in node_ids}
    order = list(node_ids)
    for _ in range(rounds):
        random.shuffle(order); changed = False
        for n in order:
            nb = adjU.get(n, ())
            if not nb:
                continue
            cnt = {}
            for m in nb:
                cnt[label[m]] = cnt.get(label[m], 0) + 1
            best = max(cnt.values())
            winner = sorted(l for l, c in cnt.items() if c == best)[0]
            if label[n] != winner:
                label[n] = winner; changed = True
        if not changed:
            break
    comms = {}
    for n, l in label.items():
        comms.setdefault(l, []).append(n)
    return sorted(comms.values(), key=len, reverse=True)


def bfs_path(adjU, s, t):
    from collections import deque
    if s not in adjU or t not in adjU:
        return None
    prev = {s: None}; q = deque([s])
    while q:
        v = q.popleft()
        if v == t:
            break
        for m in adjU.get(v, ()):
            if m not in prev:
                prev[m] = v; q.append(m)
    if t not in prev:
        return None
    path, v = [], t
    while v is not None:
        path.append(v); v = prev[v]
    return list(reversed(path))


def bfs_order(adj, start, allowed=None):
    """Breadth-first traversal from `start`; returns [(node, depth), …] in visit order.
    `allowed` (a set) restricts which nodes may be visited (node-type/kind filtering)."""
    from collections import deque
    seen = {start}; order = []; q = deque([(start, 0)])
    while q:
        v, d = q.popleft(); order.append((v, d))
        for m in sorted(adj.get(v, ())):
            if m not in seen and (allowed is None or m in allowed):
                seen.add(m); q.append((m, d + 1))
    return order


def dfs_order(adj, start, allowed=None):
    """Depth-first traversal from `start`; returns [(node, depth), …] in visit order.
    `allowed` (a set) restricts which nodes may be visited."""
    seen, order = set(), []
    def rec(v, d):
        if v in seen:
            return
        seen.add(v); order.append((v, d))
        for m in sorted(adj.get(v, ())):
            if allowed is None or m in allowed:
                rec(m, d + 1)
    rec(start, 0)
    return order


def unexplained_edges(nodes, edges):
    """Typed relations with no stated reason anywhere — not on the link, and not in
    either page's body prose about the same pair. A `related` link nobody explained
    asserts a connection the wiki never justifies, which is a content defect a
    structural check cannot see."""
    ctx = {}
    for e in edges:
        if e["type"] == "mentions" and e.get("context"):
            ctx[(e["source"], e["target"])] = True
    out = []
    for e in edges:
        if e["type"] not in ("related", "contradicts") or e.get("context"):
            continue
        a, b = e["source"], e["target"]
        if ctx.get((a, b)) or ctx.get((b, a)):
            continue
        out.append([a, b, e["type"]])
    return out


def cmd_lint(args):
    """Report what `build` will normalize in this wiki, and the content notes it cannot.

    Nothing here blocks a build: structure is normalized automatically. What remains are
    things only an author can supply \u2014 a reason for a link, a locator for a source.
    """
    wiki = args.wiki_dir
    if not glob.glob(os.path.join(wiki, "*.md")):
        print("LINT %s\n  no .md files found" % wiki); sys.exit(1)
    tmp = tempfile.mkdtemp(prefix="wiki-lint-")
    notes = []
    try:
        norm = normalize_wiki(wiki, tmp)
        for f in sorted(glob.glob(os.path.join(tmp, "*.md"))):
            stem = os.path.splitext(os.path.basename(f))[0]
            base = os.path.basename(f)
            if stem.lower() == "readme":
                continue
            _title, sections, meta = parse_page(f)
            ntype = node_type_for(stem, meta)
            if ntype in ("index", "log"):
                continue
            if ntype == "concept" and meta.get("kind") and meta["kind"] not in KINDS:
                notes.append(("unknown-kind", base, "kind: %s is not in the vocabulary (%s)"
                              % (meta["kind"], ", ".join(sorted(KINDS)))))
            if ntype == "source" and not meta.get("locator"):
                notes.append(("no-locator", base, "a source with no locator cannot be matched "
                              "to citations of the same artifact"))
            if ntype == "concept" and not any(edge_type_for(sec, DEFAULT_MAP) == "cites"
                                              for sec in sections):
                notes.append(("uncited", base, "cites no source \u2014 its claims cannot be traced"))
            for sec, lines in sections.items():
                et = edge_type_for(sec, DEFAULT_MAP)
                if et not in ("related", "contradicts"):
                    continue
                for t, info in link_contexts("\n".join(lines), subject_rule=(et == "contradicts")).items():
                    if info["typed"] and not info["context"]:
                        notes.append(("no-reason", "%s \u00b7 ## %s" % (base, sec),
                                      "[[%s]] is given no reason on the link" % t))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("LINT %s" % wiki)
    done = report_lines(norm)
    print("  build normalizes automatically:" if done else
          "  structure: already in the page contract")
    for d in done:
        print("    - " + d)
    by = {}
    for code, where, msg in notes:
        by.setdefault(code, []).append((where, msg))
    if by:
        print("  content notes (informational; none of these block a build):")
    lim = args.limit if args.limit else 3
    for code, rows in sorted(by.items(), key=lambda x: -len(x[1])):
        print("    %s \u00d7%d" % (code, len(rows)))
        for where, msg in rows[:lim]:
            print("      %s \u2014 %s" % (where, msg))
        if len(rows) > lim:
            print("      \u2026 and %d more" % (len(rows) - lim))
    print("  RESULT: %d content note(s)" % len(notes))
    sys.exit(1 if (args.strict and notes) else 0)


def cmd_validate(args):
    g, nodes, edges = load_graph(args.graph)
    ids = set(nodes)
    dangling = [[e["source"], e["target"]] for e in edges if e["target"] not in ids or e["source"] not in ids]
    selfl = [[e["source"], e["type"]] for e in edges if e["source"] == e["target"]]
    cdeg = {n: 0 for n in nodes}
    for e in edges:
        if e["type"] in CONCEPT_EDGE:
            if e["source"] in cdeg: cdeg[e["source"]] += 1
            if e["target"] in cdeg: cdeg[e["target"]] += 1
    orphans = [n for n, nd in nodes.items() if nd.get("type") == "concept" and cdeg[n] == 0]
    dedges = {x.strip() for x in args.dag_edges.split(",") if x.strip()}
    dag = dag_report(nodes, edges, dedges)
    # Only structural defects fail validation. Cycles over `mentions`/`related` are
    # EXPECTED (body cross-references aren't a DAG), so the DAG check is informational.
    problems = len(dangling) + len(orphans) + len(selfl)
    print(f"VALIDATE {args.graph}")
    print(f"  nodes: {len(nodes)}  edges: {len(edges)}")
    print(f"  dangling links : {len(dangling)} {dangling[:5]}")
    print(f"  orphan concepts: {len(orphans)} {orphans[:5]}")
    print(f"  self-loops     : {len(selfl)} {selfl[:5]}")
    unex = unexplained_edges(nodes, edges)
    print(f"  [info] links with no stated reason: {len(unex)}"
          + (f"  (e.g. {unex[0][0]} -{unex[0][2]}-> {unex[0][1]})" if unex else "")
          + "  \u2014 see `query <graph> unexplained`")
    nsrc = [nd for nd in nodes.values() if nd.get("type") == "source"]
    topics = {t for nd in nodes.values() for t in nd.get("topics") or []}
    print(f"  [info] sources with a year: {sum(1 for nd in nsrc if nd.get('year'))}/{len(nsrc)}"
          f"  · topics: {len(topics)}  — see `query <graph> timeline` and `topics`")
    print(f"  [info] DAG over {sorted(dedges)}: "
          f"{'acyclic' if dag['acyclic'] else 'has cycles (expected for cross-references)'}")
    print(f"  RESULT: {'PASS' if problems == 0 else str(problems)+' issue group(s)'}")
    sys.exit(0 if problems == 0 else 1)


def resolve_node(nodes, name):
    """A page name as a person would say it -> node id, or None.

    Tries the id, then the title, then every alias. A wiki links a page by its filename
    as often as by its title ([[Hoffmann 2022]] for "Training Compute-Optimal Large
    Language Models"), and in conversation people name pages the way they are linked;
    every node records both forms as aliases."""
    s = slug(name)
    if s in nodes:
        return s
    low = name.strip().lower()
    for n in nodes.values():
        if n["title"].lower() == low:
            return n["id"]
    for n in nodes.values():
        if any(a.lower() == low or slug(a) == s for a in (n.get("aliases") or [])):
            return n["id"]
    # A source is also named by its citation, "Cao et al., 2026" or "Cao 2026", taken from
    # the parenthetical that ends its title. Only an unambiguous match resolves.
    hits = citation_matches(nodes, name)
    return hits[0] if len(hits) == 1 else None


def citation_key(text):
    return " ".join(w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in ("et", "al", "and"))


def citation_matches(nodes, name):
    """Node ids whose title ends in a citation matching `name` ("Johnson and Cook, 1983")."""
    want = citation_key(name)
    if not want or not re.search(r"\d{4}", want):
        return []
    out = []
    for n in nodes.values():
        m = re.search(r"\(([^()]*\d{4}[^()]*)\)\s*$", n.get("title") or "")
        if m and (citation_key(m.group(1)) == want or citation_key(m.group(1)).split()[:1] + re.findall(r"\d{4}", m.group(1))[-1:] == want.split()):
            out.append(n["id"])
    return sorted(out)


def cmd_analyze(args):
    from collections import Counter
    g, nodes, edges = load_graph(args.graph)
    cids = [n for n, nd in nodes.items() if nd.get("type") == "concept"]
    types = ({x.strip() for x in args.edges.split(",") if x.strip()} if args.edges
             else set(CONCEPT_EDGE))
    adj = _adj(cids, edges, types)
    adjU = _adj(cids, edges, types, undirected=True)
    N = args.top

    print(f"ANALYZE {args.graph}")
    print(f"  concepts: {len(cids)}   edges considered {sorted(types)}: "
          f"{sum(len(v) for v in adj.values())}")
    print(f"  kind distribution : {dict(Counter(nodes[i].get('kind') for i in cids))}")
    print(f"  edge-type totals  : {dict(Counter(e['type'] for e in edges))}")

    pr = pagerank(cids, adj)
    print(f"\n  Top {N} by PageRank (influence hubs):")
    for n in sorted(cids, key=lambda x: pr[x], reverse=True)[:N]:
        print(f"    {pr[n]:.4f}  {nodes[n]['title']}  [{nodes[n].get('kind')}]")

    indeg = Counter();
    for e in edges:
        if e["type"] in types and e["target"] in nodes:
            indeg[e["target"]] += 1
    print(f"\n  Top {N} most depended-upon (in-degree):")
    for n, c in indeg.most_common(N):
        print(f"    {c:>3}  {nodes[n]['title']}")

    con = Counter()
    for e in edges:
        if e["type"] == "contradicts":
            for x in (e["source"], e["target"]):
                if x in nodes: con[x] += 1
    if con:
        print(f"\n  Most contested (contradicts degree):")
        for n, c in con.most_common(N):
            print(f"    {c:>3}  {nodes[n]['title']}")

    comps = weak_components(cids, adjU)
    print(f"\n  Weakly-connected components: {len(comps)} (largest {len(comps[0]) if comps else 0})")
    comms = label_propagation(cids, adjU)
    print(f"  Communities (label propagation): {len(comms)}")
    for i, c in enumerate(comms[:8], 1):
        names = ", ".join(nodes[x]["title"] for x in sorted(c)[:6])
        print(f"    C{i} ({len(c)}): {names}{' …' if len(c) > 6 else ''}")

    if args.path:
        ends = [resolve_node(nodes, x) for x in args.path]
        missing = [x for x, i in zip(args.path, ends) if i is None]
        outside = [x for x, i in zip(args.path, ends) if i is not None and i not in adjU]
        if missing:
            pretty = "no node matching " + ", ".join("'%s'" % x for x in missing)
        elif outside:
            pretty = ("%s is not a concept page; analyze measures paths between concepts. "
                      "Use `query <graph> path` to include sources." % ", ".join("'%s'" % x for x in outside))
        else:
            p = bfs_path(adjU, ends[0], ends[1])
            pretty = " → ".join(nodes[x]["title"] for x in p) if p else "no path"
        print(f"\n  Shortest path {args.path[0]} — {args.path[1]}: {pretty}")


ALL_EDGE_TYPES = ["mentions", "related", "contradicts", "cites", "indexes", "records"]


def _csv(s):
    return {x.strip() for x in s.split(",") if x.strip()} if s else None


def _years(s):
    """'2014-2020' | '2020' | '2020-' | '-2020' -> (from, to), either end None if open."""
    if not s:
        return None, None
    m = re.fullmatch(r"\s*(\d{4})?\s*([-–:])?\s*(\d{4})?\s*", s)
    if not m or not (m.group(1) or m.group(3)):
        print("--years takes YYYY, YYYY-YYYY, YYYY- or -YYYY"); sys.exit(1)
    a = int(m.group(1)) if m.group(1) else None
    b = int(m.group(3)) if m.group(3) else None
    return (a, a) if not m.group(2) else (a, b)


def cmd_query(args):
    """Canned graph questions — callers never write raw SQL or graph code.

    Filtering (any combination):
      edge types:  --edges a,b (only these)   --ignore-edges x,y (all but these)
      node kinds:  --kind a,b                  --ignore-kind x,y
      node types:  --node-type a,b             --ignore-node-type x,y
    """
    g, nodes, edges = load_graph(args.graph)
    def title(i): return nodes[i]["title"] if i in nodes else i
    def resolve(name):
        return resolve_node(nodes, name)

    # ---- resolve include/exclude filters ----
    inc_e, exc_e = _csv(args.edges), _csv(args.ignore_edges) or set()
    inc_k, exc_k = _csv(args.kind), _csv(args.ignore_kind) or set()
    inc_t, exc_t = _csv(args.node_type), _csv(args.ignore_node_type) or set()
    inc_topic = [t.lower() for t in parse_topics(args.topic)] if args.topic else None
    y_from, y_to = _years(args.years)

    def edge_types(default):
        base = inc_e if inc_e is not None else set(default)
        return base - exc_e
    def node_ok(i):
        nd = nodes.get(i, {})
        k, t = nd.get("kind"), nd.get("type")
        if inc_k is not None and k not in inc_k: return False
        if k in exc_k: return False
        if inc_t is not None and t not in inc_t: return False
        if t in exc_t: return False
        if inc_topic is not None and not topic_matches(nd.get("topics"), inc_topic): return False
        if (y_from is not None or y_to is not None) and not nd.get("year"): return False
        if y_from is not None and nd["year"] < y_from: return False
        if y_to is not None and nd["year"] > y_to: return False
        return True

    q = args.question

    if q == "list":
        for n in sorted((x for x in nodes.values() if node_ok(x["id"])), key=lambda x: x["id"]):
            extra = "  ".join(x for x in (str(n.get("year") or ""), ", ".join(n.get("topics") or [])) if x)
            print(f'{n["id"]:34} {str(n.get("kind")):9} {n["type"]:8} in={n.get("in_degree",0):<3} '
                  f'out={n.get("out_degree",0):<3}' + (f'  {extra}' if extra else ''))
        return
    if q == "topics":
        rows = {}
        for n in nodes.values():
            if not node_ok(n["id"]):
                continue
            for t in n.get("topics") or []:
                r = rows.setdefault(t, {"source": 0, "concept": 0, "years": []})
                if n["type"] in ("source", "concept"):
                    r[n["type"]] += 1
                if n["type"] == "source" and n.get("year"):
                    r["years"].append(n["year"])
        for t in sorted(rows):
            r = rows[t]
            span = (f'{min(r["years"])}–{max(r["years"])}' if r["years"] else "undated")
            print(f'{t:58} sources={r["source"]:<3} concepts={r["concept"]:<3} {span}')
        untagged = sum(1 for n in nodes.values() if n["type"] in ("source", "concept")
                       and node_ok(n["id"]) and not n.get("topics"))
        print(f"\n  {len(rows)} topic(s); {untagged} source/concept page(s) with no topic")
        return
    if q == "timeline":
        dated = sorted((n for n in nodes.values() if n.get("year") and node_ok(n["id"])),
                       key=lambda n: (n["year"], n["type"] != "source", n["title"]))
        cur = None
        for n in dated:
            if n["year"] != cur:
                cur = n["year"]; print(cur)
            tag = n.get("kind") or n["type"]
            derived = "  (earliest cited source)" if n.get("year_basis") == "earliest cited source" else ""
            print(f'  [{tag}] {n["title"]}{derived}'
                  + (f'  — {", ".join(n["topics"])}' if n.get("topics") else ""))
        undated = sum(1 for n in nodes.values() if not n.get("year") and node_ok(n["id"]))
        print(f"\n  {len(dated)} dated node(s); {undated} undated")
        return
    if q == "bridges":
        # Links between pages that share no topic: where one subject reaches into another.
        types = edge_types(["related", "contradicts", "mentions", "cites"])
        field = lambda ts: {t.split(" / ")[0] for t in ts}
        seen, crossings = set(), 0
        count = 0
        for e in edges:
            a, b = nodes.get(e["source"]), nodes.get(e["target"])
            if e["type"] not in types or not a or not b or not (node_ok(a["id"]) and node_ok(b["id"])):
                continue
            ta, tb = a.get("topics") or [], b.get("topics") or []
            if not ta or not tb or set(ta) & set(tb):
                continue
            key = (e["type"],) + (tuple(sorted((a["id"], b["id"]))) if e["type"] in SYMMETRIC
                                  else (a["id"], b["id"]))
            if key in seen:
                continue
            seen.add(key); count += 1
            other_field = not (field(ta) & field(tb))
            crossings += other_field
            print(f'  {a["title"]} [{ta[0]}]  -{e["type"]}->  {b["title"]} [{tb[0]}]'
                  + ("  (across fields)" if other_field else ""))
            if e.get("context"):
                print(f'      {e["context"]}')
        print(f"\n  {count} link(s) between pages that share no topic; "
              f"{crossings} of them join different fields")
        return
    if q == "unexplained":
        rows = unexplained_edges(nodes, edges)
        for a, b, t in rows:
            if node_ok(a) and node_ok(b):
                print(f"  {nodes[a]['title']}  -{t}->  {nodes[b]['title']}")
        print(f"\n  {len(rows)} typed link(s) with no reason on the link and none in either "
              f"page's body. Add \u201c \u2014 why\u201d after the link, or remove it.")
        return

    if q == "contradicts":
        seen = set()
        for e in edges:
            if e["type"] == "contradicts" and node_ok(e["source"]) and node_ok(e["target"]):
                k = tuple(sorted((e["source"], e["target"])))
                if k not in seen:
                    seen.add(k); print(f'{title(k[0])}  <->  {title(k[1])}')
        return
    if q == "kind":
        want = args.terms[0].lower() if args.terms else None
        for n in nodes.values():
            if str(n.get("kind")).lower() == want:
                print(f'{n["id"]:34} {n["title"]}')
        return
    if q == "edgetype":
        want = args.terms[0] if args.terms else None
        for e in edges:
            if e["type"] == want and node_ok(e["source"]) and node_ok(e["target"]):
                w = f' x{e["weight"]}' if e.get("weight", 1) > 1 else ""
                print(f'{title(e["source"])}  -{want}->  {title(e["target"])}{w}')
        return
    if q == "path":
        if len(args.terms) < 2:
            print("usage: query <graph> path A B"); sys.exit(1)
        types = edge_types(["mentions", "related", "contradicts", "cites"])
        allowed = {i for i in nodes if node_ok(i)}
        sub = [e for e in edges if e["source"] in allowed and e["target"] in allowed]
        adjU = _adj(list(nodes), sub, types, undirected=True)
        a, b = resolve(args.terms[0]), resolve(args.terms[1])
        p = bfs_path(adjU, a, b) if a and b else None
        print(" → ".join(title(x) for x in p) if p else "no path (with current filters)")
        return

    if q == "lineage":
        # Chains of citation between SOURCE pages: FROM cites X cites ... cites TO. `path`
        # is undirected and happily routes through a shared concept page, which says two
        # papers are about the same thing, not that one builds on the other.
        if len(args.terms) < 2:
            print("usage: query <graph> lineage FROM TO   (FROM cites … cites TO)"); sys.exit(1)
        a, b = resolve(args.terms[0]), resolve(args.terms[1])
        for t, i in zip(args.terms, (a, b)):
            several = [] if i else citation_matches(nodes, t)
            if len(several) > 1:
                print("'%s' matches %d pages; name one:\n  %s" % (t, len(several), "\n  ".join(several)))
                sys.exit(1)
        missing = [t for t, i in zip(args.terms, (a, b)) if not i]
        if missing:
            print("no node matching " + ", ".join("'%s'" % t for t in missing)); sys.exit(1)
        adj = {}
        for e in edges:
            s, t = nodes.get(e["source"], {}), nodes.get(e["target"], {})
            if e["type"] == "cites" and s.get("type") == "source" and t.get("type") == "source":
                adj.setdefault(e["source"], set()).add(e["target"])

        def cite_label(i):
            m = re.search(r"\(([^()]*\d{4}[^()]*)\)\s*$", title(i))
            return m.group(1) if m else None
        seen_labels = {}
        for i in nodes:
            if cite_label(i):
                seen_labels[cite_label(i)] = seen_labels.get(cite_label(i), 0) + 1

        def label(i):
            t, c = title(i), cite_label(i)
            if c and seen_labels[c] == 1:
                return c
            if c:   # two "Cao et al., 2026": add the start of each title so the chain is readable
                return "%s [%s…]" % (c, " ".join(t.split()[:4]))
            return t if len(t) <= 60 else t[:59] + "…"

        def chains(start, goal):
            found = []
            def walk(v, path):
                if v == goal:
                    found.append(path); return
                if len(path) - 1 >= args.max_depth:
                    return
                for w in sorted(adj.get(v, ())):
                    if w not in path and (w == goal or node_ok(w)):
                        walk(w, path + [w])
            walk(start, [start])
            return sorted(found, key=lambda p: (len(p), [label(x) for x in p]))

        paths = chains(a, b)
        if not paths:
            back = chains(b, a)
            print(f"no citation chain from {label(a)} back to {label(b)} within {args.max_depth} step(s)"
                  + (f"; {len(back)} run the other way — try `lineage \"{args.terms[1]}\" \"{args.terms[0]}\"`"
                     if back else ""))
            return
        print(f"{len(paths)} citation chain(s) from {label(a)} back to {label(b)} "
              f"(≤{args.max_depth} steps; shortest {len(paths[0]) - 1})")
        for p in paths[:50]:
            print("  " + "  →  ".join(label(x) for x in p))
        if len(paths) > 50:
            print(f"  … and {len(paths) - 50} more")
        through = {}
        for p in paths:
            for x in p[1:-1]:
                through[x] = through.get(x, 0) + 1
        if through:
            print("\n  papers the chains pass through most:")
            for x, c in sorted(through.items(), key=lambda kv: (-kv[1], label(kv[0])))[:10]:
                print(f"    {c:>3}  {label(x)}")
        return

    # node-scoped questions
    if not args.terms:
        print(f"'{q}' needs a node name"); sys.exit(1)
    nid = resolve(args.terms[0])
    if not nid:
        print(f"no node matching '{args.terms[0]}'"); sys.exit(1)

    if q in ("bfs", "dfs"):
        types = edge_types(["mentions", "related", "contradicts", "cites"])
        allowed = {i for i in nodes if node_ok(i)} | {nid}
        adj = _adj(list(nodes), edges, types, undirected=args.undirected)
        order = (bfs_order if q == "bfs" else dfs_order)(adj, nid, allowed)
        print(f"{q.upper()} from {title(nid)}  (edges={sorted(types)}, "
              f"{'undirected' if args.undirected else 'directed'}, {len(order)} nodes)")
        for v, d in order:
            print("  " * d + f'{title(v)}  [{nodes[v].get("kind") or nodes[v]["type"]}]')
        return
    if q == "node":
        n = nodes[nid]; keep = edge_types(ALL_EDGE_TYPES)
        print(f'{n["title"]}  [{n.get("kind") or n["type"]}]  in={n.get("in_degree",0)} out={n.get("out_degree",0)}'
              + (f'  {n.get("n_sources")} source(s)' if n.get("n_sources") is not None else ''))
        if n.get("year"):
            print(f'year: {n["year"]}  ({n.get("year_basis")})')
        if n.get("topics"):
            print(f'topics: {", ".join(n["topics"])}'
                  + (f'  ({n["topics_basis"]})' if n.get("topics_basis") else ""))
        if n.get("summary"): print(n["summary"])
        print("outgoing:")
        for e in n.get("edges", []):
            if e["type"] in keep and node_ok(e["target"]):
                print(f'  -{e["type"]}->  {title(e["target"])}')
        return
    if q == "neighbors":
        keep = edge_types(ALL_EDGE_TYPES)
        for e in edges:
            if e["source"] == nid and e["type"] in keep and node_ok(e["target"]):
                print(f'  -{e["type"]}->  {title(e["target"])}')
        return
    if q == "backlinks":
        keep = edge_types(ALL_EDGE_TYPES)
        for e in edges:
            if e["target"] == nid and e["type"] in keep and node_ok(e["source"]):
                print(f'  {title(e["source"])}  -{e["type"]}->')
        return


def find_page(wiki_dir, name):
    target = slug(name)
    for f in glob.glob(os.path.join(wiki_dir, "*.md")):
        stem = os.path.splitext(os.path.basename(f))[0]
        title, _s, _m = parse_page(f)
        if slug(title) == target or slug(stem) == target:
            return f
    return None


SECTION_FOR = {"related": "Related", "contradicts": "Contradictions / tensions",
               "mentions": "Explanation", "cites": "Sources"}


def split_frontmatter(txt):
    """-> (fields, key_order, body). Missing frontmatter yields ({}, [], txt)."""
    lines = txt.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, [], txt
    fm, order, j = {}, [], 1
    while j < len(lines) and lines[j].strip() != "---":
        m = re.match(r"\s*([A-Za-z_][\w-]*)\s*:\s*(.*?)\s*$", lines[j])
        if m:
            k = m.group(1).lower()
            fm[k] = m.group(2)
            order.append(k)
        j += 1
    return fm, order, "\n".join(lines[j + 1:]).lstrip("\n")


def join_frontmatter(fm, order, body):
    keys = order + [k for k in fm if k not in order]
    rows = ["%s: %s" % (k, fm[k]) for k in keys if fm.get(k)]
    return "---\n" + "\n".join(rows) + "\n---\n\n" + body


def link_names_for(wiki_dir, name):
    """Every spelling a [[link]] to `name` might use: given name, H1 title, filename stem."""
    out = {name}
    f = find_page(wiki_dir, name)
    if f:
        out.add(parse_page(f)[0])
        out.add(os.path.splitext(os.path.basename(f))[0])
    return {x for x in out if x}


def link_pattern(names):
    return re.compile(r"\[\[\s*(?:%s)\s*(\|[^\]]*)?\]\]"
                      % "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True)), re.I)


def cmd_update(args):
    """Edit the SOURCE wiki markdown (single source of truth); re-run build to regenerate."""
    wd, act = args.wiki_dir, args.action

    if act in ("add-node", "add-source"):
        if not args.title:
            print("%s needs --title" % act); sys.exit(1)
        path = os.path.join(wd, args.title + ".md")
        if os.path.exists(path):
            print("already exists:", path); sys.exit(1)
        if act == "add-source":
            if not args.locator:
                print("add-source needs --locator (a path, URL, or doi:/isbn:/arxiv: id)")
                sys.exit(1)
            fm = {"type": "source", "locator": args.locator,
                  "medium": (args.medium or medium_for(args.locator) or "document")}
            for k in ("author", "date"):
                if getattr(args, k, None):
                    fm[k] = getattr(args, k)
            if args.topics:
                fm["topics"] = ", ".join(parse_topics(args.topics))
            order = ["type", "medium", "locator", "author", "date", "topics"]
            body = ("# %s\n\n## Summary\n%s\n\n## Explanation\n%s\n\n## Related\n\n"
                    % (args.title, args.summary or "", args.explanation or ""))
            open(path, "w", encoding="utf-8").write(join_frontmatter(fm, order, body))
            print("created source", path, "(%s)" % fm["medium"])
        else:
            kind = (args.kind or "concept").lower()
            if kind not in KINDS:
                print("--kind must be one of:", ", ".join(sorted(KINDS))); sys.exit(1)
            topics_line = ("topics: %s\n" % ", ".join(parse_topics(args.topics))
                           if args.topics else "")
            open(path, "w", encoding="utf-8").write(
                "---\nkind: %s\n%s---\n\n# %s\n\n## Summary\n%s\n\n"
                "## Explanation\n%s\n\n## Related\n\n"
                "## Contradictions / tensions\n\n## Sources\n"
                % (kind, topics_line, args.title, args.summary or "", args.explanation or ""))
            print("created", path)

    elif act == "add-edge":
        if args.type not in SECTION_FOR:
            print("--type must be one of:", ", ".join(sorted(SECTION_FOR))); sys.exit(1)
        src = find_page(wd, args.frm or "")
        if not src:
            print("no source page for --from", args.frm); sys.exit(1)
        tgt = find_page(wd, args.to or "")
        tgt_title = parse_page(tgt)[0] if tgt else args.to
        header = "## " + SECTION_FOR[args.type]
        # A `## Sources` entry is a literal citation line, not a [[link]]: prefer the
        # target's declared locator so the bullet resolves onto the authored source page.
        if args.type == "cites":
            loc = parse_page(tgt)[2].get("locator") if tgt else None
            entry = "- %s — %s" % (loc, tgt_title) if loc else "- [[%s]]" % tgt_title
        else:
            entry = "[[%s]]" % tgt_title
        lines = open(src, encoding="utf-8").read().split("\n")
        idx = next((k for k, l in enumerate(lines) if l.strip() == header), -1)
        if idx == -1:
            lines += ["", header, "", entry]
        else:
            lines.insert(idx + 1, entry)
        open(src, "w", encoding="utf-8").write("\n".join(lines))
        warn = "" if tgt else "  (warning: no page named '%s' yet — link will be dangling)" % args.to
        print('added %s to "%s" of %s%s' % (entry.strip("- "), SECTION_FOR[args.type],
                                            os.path.basename(src), warn))

    elif act == "remove-edge":
        src = find_page(wd, args.frm or "")
        if not src:
            print("no source page for --from", args.frm); sys.exit(1)
        names = link_names_for(wd, args.to or "")
        if not names:
            print("remove-edge needs --to"); sys.exit(1)
        pat = link_pattern(names)
        want = SECTION_FOR.get(args.type) if args.type else None
        out, sec, removed = [], None, 0
        for line in open(src, encoding="utf-8").read().split("\n"):
            m = H2_RE.match(line)
            if m:
                sec = m.group(1).strip()
                out.append(line); continue
            if want is None or sec == want:
                new = pat.sub("", line)
                if new != line:
                    removed += len(pat.findall(line))
                    stripped = new.strip().lstrip("-*·").strip()
                    if not stripped or stripped in ("—", "-"):
                        continue                      # bullet held only that link
                    line = new
            out.append(line)
        open(src, "w", encoding="utf-8").write("\n".join(out))
        scope = 'section "%s"' % want if want else "all sections"
        print("removed %d link(s) to '%s' from %s of %s"
              % (removed, args.to, scope, os.path.basename(src)))

    elif act == "remove-node":
        p = find_page(wd, args.node or "")
        if not p:
            print("no page for --node", args.node); sys.exit(1)
        names = link_names_for(wd, args.node)
        pat = link_pattern(names)
        inbound = []
        for f in sorted(glob.glob(os.path.join(wd, "*.md"))):
            if os.path.abspath(f) == os.path.abspath(p):
                continue
            if pat.search(CODE_RE.sub("", open(f, encoding="utf-8").read())):
                inbound.append(os.path.basename(f))
        os.remove(p)
        print("deleted", os.path.basename(p))
        if inbound:
            print("  WARNING: %d page(s) still link here and will now dangle: %s"
                  % (len(inbound), ", ".join(inbound)))
            print("  fix with: update <wiki> remove-edge --from <page> --to '%s'" % args.node)

    elif act == "rename":
        p = find_page(wd, args.node or "")
        if not p:
            print("no page for --node", args.node); sys.exit(1)
        if not args.title:
            print("rename needs --title (the new title)"); sys.exit(1)
        old_names = link_names_for(wd, args.node)
        # H1_RE is not MULTILINE — it is applied per line everywhere else, and these
        # files usually open with frontmatter, so a whole-text search never matches.
        lines = open(p, encoding="utf-8").read().split("\n")
        for i, l in enumerate(lines):
            if H1_RE.match(l):
                lines[i] = "# " + args.title
                break
        else:                                   # no H1: insert one after any frontmatter
            at = 0
            if lines and lines[0].strip() == "---":
                at = next((k for k in range(1, len(lines))
                           if lines[k].strip() == "---"), 0) + 1
                while at < len(lines) and not lines[at].strip():
                    at += 1
            lines[at:at] = ["# " + args.title, ""]
        open(p, "w", encoding="utf-8").write("\n".join(lines))
        newp = os.path.join(wd, args.title + ".md")
        if os.path.abspath(newp) != os.path.abspath(p):
            if os.path.exists(newp):
                print("target filename already exists:", newp); sys.exit(1)
            os.rename(p, newp)
        pat = link_pattern(old_names)
        touched = 0
        for f in sorted(glob.glob(os.path.join(wd, "*.md"))):
            t = open(f, encoding="utf-8").read()
            nt = pat.sub(lambda m: "[[%s%s]]" % (args.title, m.group(1) or ""), t)
            if nt != t:
                open(f, "w", encoding="utf-8").write(nt); touched += 1
        print("renamed to '%s' (%s); rewrote links in %d page(s)"
              % (args.title, os.path.basename(newp), touched))

    elif act == "set-topics":
        p = find_page(wd, args.node or "")
        if not p:
            print("no page for --node", args.node); sys.exit(1)
        fm, order, body = split_frontmatter(open(p, encoding="utf-8").read())
        topics = parse_topics(args.topics)
        if topics:
            fm["topics"] = ", ".join(topics)
            if "topics" not in order:
                order.append("topics")
        else:                                   # --topics "" clears them
            fm.pop("topics", None); order = [k for k in order if k != "topics"]
        open(p, "w", encoding="utf-8").write(join_frontmatter(fm, order, body))
        print("set topics=%s on %s" % (", ".join(topics) or "(none)", os.path.basename(p)))

    elif act in ("set-kind", "set-type"):
        p = find_page(wd, args.node or "")
        if not p:
            print("no page for --node", args.node); sys.exit(1)
        field = "kind" if act == "set-kind" else "type"
        val = (args.kind if act == "set-kind" else args.type or "")
        val = (val or "").lower()
        allowed = KINDS if act == "set-kind" else NODE_TYPES
        if val not in allowed:
            print("--%s must be one of: %s" % (field, ", ".join(sorted(allowed)))); sys.exit(1)
        fm, order, body = split_frontmatter(open(p, encoding="utf-8").read())
        fm[field] = val
        if field not in order:
            order.insert(0, field)
        if val != "concept" and field == "type" and "kind" in fm:
            # a source/index/log node holds no knowledge kind
            fm.pop("kind"); order = [k for k in order if k != "kind"]
            print("  (dropped `kind`: it classifies knowledge, and only concepts carry it)")
        open(p, "w", encoding="utf-8").write(join_frontmatter(fm, order, body))
        print("set %s=%s on %s" % (field, val, os.path.basename(p)))

    print("→ re-run `build` to regenerate the graph.")


def main():
    ap = argparse.ArgumentParser(description="LLM wiki -> knowledge-space graph toolkit.")
    sub = ap.add_subparsers(dest="cmd")

    b = sub.add_parser("build", help="parse a wiki folder into graph.json")
    b.add_argument("wiki_dir")
    b.add_argument("-o", "--out", default="graph.json")
    b.add_argument("--emit", default="", help="comma list: sqlite,graphml")
    b.add_argument("--exclude", default="readme",
                   help="filename stems to skip (index/log are INCLUDED as hub nodes by default)")
    b.add_argument("--stubs", action="store_true", help="create nodes for dangling links")
    b.add_argument("--dag-edges", default="mentions", help="edge types to check for acyclicity")
    b.add_argument("--kst", action="store_true", help="also emit domain.json (KST candidate)")
    b.add_argument("--map", default=None, help="JSON file overriding section->edge map")
    b.add_argument("--vocab", default=None,
                   help="JSON file overriding the kind/edge vocabulary")
    b.add_argument("--no-normalize", action="store_true",
                   help="parse the wiki exactly as written (skip structural normalization)")
    b.add_argument("--emit-normalized", default=None, metavar="DIR",
                   help="also keep the normalized wiki in DIR (must be empty)")
    b.set_defaults(func=cmd_build)

    v = sub.add_parser("validate", help="check an existing graph.json (exit 1 on issues)")
    v.add_argument("graph")
    v.add_argument("--dag-edges", default="mentions")
    v.add_argument("--vocab", default=None,
                   help="JSON file overriding the kind/edge vocabulary")
    v.set_defaults(func=cmd_validate)

    a = sub.add_parser("analyze", help="graph metrics over an existing graph.json")
    a.add_argument("graph")
    a.add_argument("--edges", default=None,
                   help="edge types to include in the analysis graph "
                        "(default: every concept edge type in the active vocabulary)")
    a.add_argument("--top", type=int, default=5)
    a.add_argument("--path", nargs=2, metavar=("A", "B"), help="shortest path between two nodes")
    a.add_argument("--vocab", default=None,
                   help="JSON file overriding the kind/edge vocabulary")
    a.set_defaults(func=cmd_analyze)

    q = sub.add_parser("query", help="ask common questions about a graph.json (no SQL needed)")
    q.add_argument("graph")
    q.add_argument("question",
                   choices=["list", "node", "neighbors", "backlinks", "kind", "edgetype",
                            "contradicts", "unexplained", "path", "bfs", "dfs",
                            "topics", "timeline", "bridges", "lineage"])
    q.add_argument("terms", nargs="*", help="node name(s), or a kind/edge-type argument")
    # filters — any combination:
    q.add_argument("--edges", default=None, help="ONLY traverse/show these edge types (comma list)")
    q.add_argument("--ignore-edges", default=None, help="traverse/show all edge types EXCEPT these")
    q.add_argument("--kind", default=None, help="ONLY visit nodes of these kinds (comma list)")
    q.add_argument("--ignore-kind", default=None, help="visit all kinds EXCEPT these")
    q.add_argument("--node-type", default=None, help="ONLY visit these structural types (concept,source,index,log)")
    q.add_argument("--ignore-node-type", default=None, help="visit all node types EXCEPT these")
    q.add_argument("--topic", default=None,
                   help="ONLY visit nodes in these topics (comma list; a field matches every topic under it)")
    q.add_argument("--years", default=None, help="ONLY visit nodes dated YYYY, YYYY-YYYY, YYYY- or -YYYY")
    q.add_argument("--undirected", action="store_true", help="treat edges as undirected in bfs/dfs")
    q.add_argument("--max-depth", type=int, default=4, help="lineage: longest citation chain to follow")
    q.add_argument("--vocab", default=None,
                   help="JSON file overriding the kind/edge vocabulary")
    q.set_defaults(func=cmd_query)

    li = sub.add_parser("lint", help="check the source markdown BEFORE building")
    li.add_argument("wiki_dir")
    li.add_argument("--strict", action="store_true", help="exit non-zero on warnings too")
    li.add_argument("--limit", type=int, default=3, help="examples to print per issue class")
    li.set_defaults(func=cmd_lint)

    u = sub.add_parser("update", help="edit the source wiki markdown, then re-run build")
    u.add_argument("wiki_dir")
    u.add_argument("action", choices=["add-node", "add-source", "add-edge", "remove-edge",
                                      "remove-node", "rename", "set-kind", "set-type",
                                      "set-topics"])
    u.add_argument("--title", help="new node title; with `rename`, the new title")
    u.add_argument("--kind", help="concept|schema|procedure|fact (concept nodes only)")
    u.add_argument("--summary"); u.add_argument("--explanation")
    u.add_argument("--from", dest="frm"); u.add_argument("--to")
    u.add_argument("--type", help="edge type for add/remove-edge; node type for set-type")
    u.add_argument("--node", help="the page to act on")
    u.add_argument("--locator", help="add-source: path, URL, or doi:/arxiv:/isbn: identifier")
    u.add_argument("--medium", help="add-source: paper|web|book|slides|video|transcript|code|…")
    u.add_argument("--author"); u.add_argument("--date")
    u.add_argument("--topics", help="add-node/add-source/set-topics: comma list, e.g. "
                                    "\"Materials engineering / Ballistic impact\"")
    u.set_defaults(func=cmd_update)

    args = ap.parse_args()
    if not getattr(args, "cmd", None):
        ap.print_help(); sys.exit(1)
    # applied before dispatch so every stage sees the same vocabulary
    load_vocab(getattr(args, "vocab", None))
    args.func(args)


if __name__ == "__main__":
    main()
