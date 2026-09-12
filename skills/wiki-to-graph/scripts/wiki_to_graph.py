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
import argparse, glob, json, os, re, sqlite3, sys, datetime, xml.sax.saxutils as sx

LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
CODE_RE = re.compile(r"`[^`]*`")
H1_RE   = re.compile(r"^#\s+(.*)$")
H2_RE   = re.compile(r"^##\s+(.*)$")

DEFAULT_MAP = [  # (predicate on lowercased section name, edge type)
    (lambda s: "contradict" in s or "tension" in s, "contradicts"),
    (lambda s: s.startswith("related"),             "related"),
    (lambda s: s.startswith("source"),              "cites"),
    (lambda s: True,                                "mentions"),  # summary/explanation/other
]
SYMMETRIC = {"related", "contradicts"}
# index.md / log.md are navigational hubs, not concepts. Their links get their own
# edge types so they don't pollute concept-level semantics (e.g. a "tensions" section
# heading in index.md must NOT be read as a `contradicts` edge).
META_EDGE = {"index": "indexes", "log": "records"}
CONCEPT_EDGE_TYPES = {"mentions", "related", "contradicts", "cites"}


NODE_TYPES = {"concept", "source", "index", "log"}

# A locator identifies the artifact a source node stands for. It is deliberately
# format-agnostic: a repo-relative file, a URL, or a registered identifier. Nothing
# here assumes academic papers or a `raw/` directory.
LOCATOR_RE = re.compile(
    r"(https?://\S+"
    r"|(?:doi|arxiv|isbn|issn|urn|hdl):\S+"
    r"|[\w./~@\-]+\.(?:pdf|md|txt|html?|epub|mobi|docx?|pptx?|xlsx?|csv|tsv|json|ya?ml"
    r"|mp4|mov|webm|mp3|wav|m4a|vtt|srt|ipynb|py|ts|js|rs|go)\b)", re.I)

MEDIUM_BY_EXT = {
    "pdf": "paper", "md": "note", "txt": "note", "html": "web", "htm": "web",
    "epub": "book", "mobi": "book", "doc": "document", "docx": "document",
    "ppt": "slides", "pptx": "slides", "xls": "data", "xlsx": "data",
    "csv": "data", "tsv": "data", "json": "data", "yaml": "data", "yml": "data",
    "mp4": "video", "mov": "video", "webm": "video", "mp3": "audio", "wav": "audio",
    "m4a": "audio", "vtt": "transcript", "srt": "transcript",
    "ipynb": "notebook", "py": "code", "ts": "code", "js": "code", "rs": "code", "go": "code",
}
MEDIUM_BY_SCHEME = {"doi": "paper", "arxiv": "paper", "isbn": "book",
                    "issn": "periodical", "urn": "document", "hdl": "document"}


def locator_in(text):
    """First locator in a string, or None."""
    m = LOCATOR_RE.search(text or "")
    return m.group(1).rstrip(".,;)") if m else None


def medium_for(loc):
    """Best-effort medium from a locator. None when it cannot be inferred."""
    if not loc:
        return None
    l = loc.strip().lower()
    if l.startswith(("http://", "https://")):
        return "web"
    scheme = l.split(":", 1)[0]
    if scheme in MEDIUM_BY_SCHEME:
        return MEDIUM_BY_SCHEME[scheme]
    ext = l.rsplit(".", 1)[-1] if "." in l else ""
    return MEDIUM_BY_EXT.get(ext)


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
    for raw in lines[i:]:
        line = raw.rstrip("\n")
        m1 = H1_RE.match(line)
        m2 = H2_RE.match(line)
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


def link_contexts(text):
    """-> {target: {"count": int, "context": str}}.

    `context` is the prose of the bullet or paragraph the link sits in. Without it
    an edge records THAT two pages are related and discards the author's statement
    of HOW, which is usually the only part a reader wants.

    Two things are deliberately NOT context. A leading "[[X]] \u2014 " is the bullet's
    subject and is already shown as the edge's label, so it is dropped. And a block
    that is only links ("[[a]] \u00b7 [[b]] \u00b7 [[c]]") has no prose at all \u2014 storing the
    sibling names would be noise, so such edges get an empty context.
    """
    out = {}
    for block in blocks_of(CODE_RE.sub("", text)):
        found = LINK_RE.findall(block)
        if not found:
            continue
        body = BULLET_RE.sub("", block.strip())
        lead = re.match(r"\s*\[\[[^\]]+\]\]\s*[\u2014\u2013:-]\s+", body)
        if lead:
            body = body[lead.end():]
        bare = re.sub(r"[\s\u00b7*+:;,.|\u2014\u2013-]+", " ", LINK_RE.sub("", body)).strip()
        if len(bare) < 12:
            ctx = ""                                  # link list, no prose
        else:
            ctx = re.sub(r"\s+", " ", strip_links(body)).strip()
            if len(ctx) > MAX_CONTEXT:
                ctx = ctx[:MAX_CONTEXT].rsplit(" ", 1)[0] + "\u2026"
        for t, _alias in found:
            t = t.strip()
            if not t or t.lower() == "wiki-links":
                continue
            e = out.setdefault(t, {"count": 0, "context": ""})
            e["count"] += 1
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
        nodes[cid] = node

        for sec, lines in p["sections"].items():
            et = edge_type_for(sec, mapping)
            text = "\n".join(lines)
            if et == "cites":
                for ln in lines:
                    b = ln.strip().lstrip("-*").strip()
                    if not b:
                        continue
                    source_strings.append(b)
                    sid = resolve_source(b)
                    if sid != cid:
                        add_edge(cid, sid, "cites", sec, 1, re.sub(r"\s+", " ", b).strip())
                continue
            for tgt, info in link_contexts(text).items():
                cnt = info["count"]
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
                add_edge(cid, tid, et, sec, cnt, info["context"])

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
            ("d_title","title","node","string"),
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
                     f'<data key="d_title">{esc(n.get("title"))}</data></node>\n')
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
                 in_degree INT,out_degree INT)""")
    c.execute("""CREATE TABLE edges(src TEXT,dst TEXT,type TEXT,via TEXT,directed INT,weight INT)""")
    for n in nodes.values():
        c.execute("INSERT INTO nodes VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                  (n["id"],n["type"],n.get("kind"),n.get("title"),n.get("summary",""),
                   n.get("explanation",""),json.dumps(n.get("sources",[])),n.get("file"),
                   n.get("word_count",0),n.get("n_sources",0),
                   n.get("in_degree",0),n.get("out_degree",0)))
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

    nodes,edges,warnings=build_graph(args.wiki_dir,exclude,mapping,args.stubs)

    ecount={}
    for e in edges: ecount[e["type"]]=ecount.get(e["type"],0)+1
    ncount={}
    for n in nodes.values(): ncount[n["type"]]=ncount.get(n["type"],0)+1
    dag=dag_report(nodes,edges,{x.strip() for x in args.dag_edges.split(",") if x.strip()})

    # multigraph=True: two nodes may be joined by several *typed* edges
    # (e.g. both `related` and `mentions`); a simple DiGraph would collapse them.
    graph={"directed":True,"multigraph":True,
           "meta":{"generator":"wiki_to_graph/0.2",
                   "generated":datetime.datetime.now().isoformat(timespec="seconds"),
                   "source_dir":os.path.normpath(args.wiki_dir),
                   "counts":{**ncount,"edges":ecount},
                   "dag_check":dag,"warnings":warnings},
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
    print(f"  [info] DAG over {sorted(dedges)}: "
          f"{'acyclic' if dag['acyclic'] else 'has cycles (expected for cross-references)'}")
    print(f"  RESULT: {'PASS' if problems == 0 else str(problems)+' issue group(s)'}")
    sys.exit(0 if problems == 0 else 1)


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
        s, t = slug(args.path[0]), slug(args.path[1])
        p = bfs_path(adjU, s, t)
        pretty = " → ".join(nodes[x]["title"] for x in p) if p else "no path"
        print(f"\n  Shortest path {args.path[0]} — {args.path[1]}: {pretty}")


ALL_EDGE_TYPES = ["mentions", "related", "contradicts", "cites", "indexes", "records"]


def _csv(s):
    return {x.strip() for x in s.split(",") if x.strip()} if s else None


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
        s = slug(name)
        if s in nodes: return s
        for n in nodes.values():
            if n["title"].lower() == name.lower(): return n["id"]
        return None

    # ---- resolve include/exclude filters ----
    inc_e, exc_e = _csv(args.edges), _csv(args.ignore_edges) or set()
    inc_k, exc_k = _csv(args.kind), _csv(args.ignore_kind) or set()
    inc_t, exc_t = _csv(args.node_type), _csv(args.ignore_node_type) or set()

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
        return True

    q = args.question

    if q == "list":
        for n in sorted((x for x in nodes.values() if node_ok(x["id"])), key=lambda x: x["id"]):
            print(f'{n["id"]:34} {str(n.get("kind")):9} {n["type"]:8} in={n.get("in_degree",0):<3} out={n.get("out_degree",0)}')
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
            order = ["type", "medium", "locator", "author", "date"]
            body = ("# %s\n\n## Summary\n%s\n\n## Explanation\n%s\n\n## Related\n\n"
                    % (args.title, args.summary or "", args.explanation or ""))
            open(path, "w", encoding="utf-8").write(join_frontmatter(fm, order, body))
            print("created source", path, "(%s)" % fm["medium"])
        else:
            kind = (args.kind or "concept").lower()
            if kind not in KINDS:
                print("--kind must be one of:", ", ".join(sorted(KINDS))); sys.exit(1)
            open(path, "w", encoding="utf-8").write(
                "---\nkind: %s\n---\n\n# %s\n\n## Summary\n%s\n\n"
                "## Explanation\n%s\n\n## Related\n\n"
                "## Contradictions / tensions\n\n## Sources\n"
                % (kind, args.title, args.summary or "", args.explanation or ""))
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
                            "contradicts", "path", "bfs", "dfs"])
    q.add_argument("terms", nargs="*", help="node name(s), or a kind/edge-type argument")
    # filters — any combination:
    q.add_argument("--edges", default=None, help="ONLY traverse/show these edge types (comma list)")
    q.add_argument("--ignore-edges", default=None, help="traverse/show all edge types EXCEPT these")
    q.add_argument("--kind", default=None, help="ONLY visit nodes of these kinds (comma list)")
    q.add_argument("--ignore-kind", default=None, help="visit all kinds EXCEPT these")
    q.add_argument("--node-type", default=None, help="ONLY visit these structural types (concept,source,index,log)")
    q.add_argument("--ignore-node-type", default=None, help="visit all node types EXCEPT these")
    q.add_argument("--undirected", action="store_true", help="treat edges as undirected in bfs/dfs")
    q.add_argument("--vocab", default=None,
                   help="JSON file overriding the kind/edge vocabulary")
    q.set_defaults(func=cmd_query)

    u = sub.add_parser("update", help="edit the source wiki markdown, then re-run build")
    u.add_argument("wiki_dir")
    u.add_argument("action", choices=["add-node", "add-source", "add-edge", "remove-edge",
                                      "remove-node", "rename", "set-kind", "set-type"])
    u.add_argument("--title", help="new node title; with `rename`, the new title")
    u.add_argument("--kind", help="concept|schema|procedure|fact (concept nodes only)")
    u.add_argument("--summary"); u.add_argument("--explanation")
    u.add_argument("--from", dest="frm"); u.add_argument("--to")
    u.add_argument("--type", help="edge type for add/remove-edge; node type for set-type")
    u.add_argument("--node", help="the page to act on")
    u.add_argument("--locator", help="add-source: path, URL, or doi:/arxiv:/isbn: identifier")
    u.add_argument("--medium", help="add-source: paper|web|book|slides|video|transcript|code|…")
    u.add_argument("--author"); u.add_argument("--date")
    u.set_defaults(func=cmd_update)

    args = ap.parse_args()
    if not getattr(args, "cmd", None):
        ap.print_help(); sys.exit(1)
    # applied before dispatch so every stage sees the same vocabulary
    load_vocab(getattr(args, "vocab", None))
    args.func(args)


if __name__ == "__main__":
    main()
