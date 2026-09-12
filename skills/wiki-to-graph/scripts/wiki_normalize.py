#!/usr/bin/env python3
"""
wiki_normalize.py — bring an LLM wiki written in any common style to the page
contract that wiki_to_graph parses. Deterministic; it writes a normalized COPY and
never edits the source wiki.

A wiki is usually written before anyone decides it will become a graph, so the
same knowledge arrives in many shapes: a README standing in for the index, a
"**Type:** paper" line where frontmatter would be, a paper written up as though it
were a concept, every disagreement collected on one hub page, no Sources section.
Each of those builds into a well-formed graph that is wrong in a way validation
cannot see. This module removes the difference, so the same content yields the
same graph whatever shape it was written in.

Rules (all deterministic, all reported):
  hub        README.md is the index when there is no index.md
  type/kind  a "**Type:** X" line becomes frontmatter; an artifact word (paper,
             book, video, website, slides, ...) makes the page a `source`
  locator    a "**File:**"-style field, or a locator on the Type line, becomes
             the source's `locator`
  title      a page with no "# H1" gets one from its filename
  sources    a concept page with no Sources section gets one, listing the source
             pages it links to
  disputes   a contradictions hub ("### item" holding "- [[side]]: claim" bullets)
             is distributed: every pair of opposing sides is recorded on both side
             pages, every topic the item names lists the competing claims, and the
             hub itself becomes an index
A page already in the contract passes through byte-for-byte unchanged.
"""
import glob
import os
import re

LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
CODE_RE = re.compile(r"`[^`]*`")
FENCE_RE = re.compile(r"^\s*```")
H1_RE = re.compile(r"^#\s+(\S.*?)\s*$")
H2_RE = re.compile(r"^##\s+(.*?)\s*$")
H3_RE = re.compile(r"^###\s+(.*?)\s*$")
BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")


# ---------------------------------------------------------------------------
# Locators: what identifies the artifact a source stands for. Format-agnostic —
# a repo-relative file, a URL, or a registered identifier.
# ---------------------------------------------------------------------------
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
    return m.group(1).rstrip(".,;)`'\"") if m else None


def medium_for(loc):
    """Best-effort medium from a locator. None when it cannot be inferred."""
    if not loc:
        return None
    low = loc.strip().lower()
    if low.startswith(("http://", "https://")):
        return "web"
    scheme = low.split(":", 1)[0]
    if scheme in MEDIUM_BY_SCHEME:
        return MEDIUM_BY_SCHEME[scheme]
    ext = low.rsplit(".", 1)[-1] if "." in low else ""
    return MEDIUM_BY_EXT.get(ext)


# ---------------------------------------------------------------------------
# Section vocabulary, shared with the parser so the two can never disagree about
# what a heading means.
# ---------------------------------------------------------------------------
def section_kind(name):
    """'contradicts' | 'related' | 'cites' | None (body prose)."""
    s = (name or "").strip().lower()
    if re.search(r"contradict|tension|disagreement|conflict", s):
        return "contradicts"
    if s.startswith("related") or s.startswith("see also") or s in ("links", "connections"):
        return "related"
    if re.match(r"(sources?|references?|citations?|bibliograph)", s):
        return "cites"
    return None


# ---------------------------------------------------------------------------
# "**Type:** X" vocabulary
# ---------------------------------------------------------------------------
_SOURCE_WORD = re.compile(
    r"\b(paper|preprint|article|book|chapter|report|thesis|dissertation|website|webpage|"
    r"web page|blog post|blog|documentation|docs|video|talk|lecture|podcast|transcript|"
    r"slide deck|slides|deck|presentation|dataset)\b")
_MEDIUM_FOR_WORD = {
    "paper": "paper", "preprint": "paper", "article": "paper", "thesis": "paper",
    "dissertation": "paper", "report": "document", "book": "book", "chapter": "book",
    "website": "web", "webpage": "web", "web page": "web", "blog": "web", "blog post": "web",
    "documentation": "web", "docs": "web", "video": "video", "talk": "video",
    "lecture": "video", "podcast": "audio", "transcript": "transcript", "slides": "slides",
    "slide deck": "slides", "deck": "slides", "presentation": "slides", "dataset": "data",
}
# Order matters: "training objective" is a procedure, "failure mode" a fact,
# "model class" a schema.
_KIND_RULES = [
    ("fact", r"\b(phenomenon|finding|result|failure|risk|effect|law|observation|"
             r"evidence|limitation|bias)\b"),
    ("procedure", r"\b(method|methodology|technique|algorithm|procedure|process|practice|"
                  r"training|objective|stage|paradigm|recipe|workflow|strategy|approach|"
                  r"protocol|optimi[sz]ation)\b"),
    ("schema", r"\b(architecture|architectural|mechanism|component|model|structure|formula|"
               r"equation|format|parameter|representation|layer|schema|framework|system)\b"),
    ("concept", r"\b(concept|idea|property|category|term|theme|principle|notion|topic|field)\b"),
]
TYPE_LINE_RE = re.compile(r"^\s*\*\*Type:\*\*\s*(.+?)\s*$", re.M)
META_FIELD_RE = re.compile(
    r"\*\*(?:file|url|link|locator|pdf|doi|arxiv|isbn)\s*:\*\*\s*`?([^`·\n]+)`?", re.I)


def classify_type(value):
    """A '**Type:**' value -> ('source', medium|None) | ('concept', kind) | (None, None)."""
    v = re.sub(r"[*_`]", "", value.split("·")[0]).strip().lower()
    m = _SOURCE_WORD.search(v)
    if m:
        return "source", _MEDIUM_FOR_WORD.get(m.group(1))
    for kind, rx in _KIND_RULES:
        if re.search(rx, v):
            return "concept", kind
    return None, None


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------
def _unfenced(lines):
    """Yield (index, line, inside_code_fence)."""
    fence = False
    for i, ln in enumerate(lines):
        if FENCE_RE.match(ln):
            yield i, ln, True
            fence = not fence
            continue
        yield i, ln, fence


def split_frontmatter(text):
    """-> (fields dict or None, body_start_line_index, lines)."""
    lines = text.split("\n")
    if lines and lines[0].strip() == "---":
        for j in range(1, len(lines)):
            if lines[j].strip() == "---":
                fm = {}
                for ln in lines[1:j]:
                    m = re.match(r"\s*([A-Za-z_][\w-]*)\s*:\s*(.*?)\s*$", ln)
                    if m:
                        fm[m.group(1).lower()] = m.group(2).strip().strip("'\"")
                return fm, j + 1, lines
    return None, 0, lines


def set_frontmatter(text, updates, order=("type", "kind", "medium", "locator")):
    """Add missing keys, creating the block if absent. Existing keys are never rewritten."""
    fm, start, lines = split_frontmatter(text)
    keys = [k for k in order if k in updates] + [k for k in updates if k not in order]
    rows = ["%s: %s" % (k, updates[k]) for k in keys if updates[k]]
    if not rows:
        return text
    if fm is None:
        return "---\n" + "\n".join(rows) + "\n---\n\n" + text.lstrip("\n")
    return "\n".join(lines[:start - 1] + rows + lines[start - 1:])


def page_title(text):
    fm, start, lines = split_frontmatter(text)
    for _i, ln, code in _unfenced(lines[start:]):
        if code:
            continue
        m = H1_RE.match(ln)
        if m:
            return m.group(1)
    return None


def preamble(text):
    """Lines before the first '## ' heading, frontmatter excluded."""
    fm, start, lines = split_frontmatter(text)
    out = []
    for _i, ln, code in _unfenced(lines[start:]):
        if not code and H2_RE.match(ln):
            break
        out.append(ln)
    return "\n".join(out)


def h2_spans(lines, start=0):
    """[(heading_index, end_index_exclusive, name)] for '## ' sections, fences respected."""
    heads = [(i, H2_RE.match(ln).group(1)) for i, ln, code in _unfenced(lines)
             if i >= start and not code and H2_RE.match(ln)]
    return [(h, heads[k + 1][0] if k + 1 < len(heads) else len(lines), name)
            for k, (h, name) in enumerate(heads)]


def links_outside_code(text):
    return [t.strip() for t, _a in LINK_RE.findall(CODE_RE.sub("", text))]


def plain(text):
    """Markup-free single line: links become their visible text."""
    t = LINK_RE.sub(lambda m: (m.group(2) or m.group(1)).strip(), text)
    return re.sub(r"\s+", " ", t).strip()


# ---------------------------------------------------------------------------
# Contradictions hubs
# ---------------------------------------------------------------------------
HUB_NAME_RE = re.compile(r"contradict|tension|disagree|dispute|debate|conflict", re.I)


def _attribution_split(bullet):
    """'[[a]], [[b]]: claim' -> ('[[a]], [[b]]', 'claim'). The first colon outside
    [[...]] separates who says it from what they say; no colon means the whole
    bullet is both."""
    depth, i = 0, 0
    while i < len(bullet):
        if bullet.startswith("[[", i):
            depth += 1; i += 2; continue
        if bullet.startswith("]]", i):
            depth = max(0, depth - 1); i += 2; continue
        if bullet[i] == ":" and depth == 0 and not bullet[max(0, i - 5):i].lower().endswith("http"):
            return bullet[:i], bullet[i + 1:]
        i += 1
    return bullet, bullet


def hub_items(text):
    """[(title, [(sides, claim)], topics)] for each '### ' item in a hub page."""
    fm, start, lines = split_frontmatter(text)
    items, cur, block = [], None, None

    def close_block():
        nonlocal block
        if cur is not None and block:
            who, claim = _attribution_split(BULLET_RE.sub("", " ".join(block).strip(), count=1))
            sides = list(dict.fromkeys(links_outside_code(who)))
            if sides:
                cur["positions"].append((sides, plain(claim)))
        block = None

    for _i, ln, code in _unfenced(lines[start:]):
        if not code and (H2_RE.match(ln) or H3_RE.match(ln)):
            close_block()
            if cur:
                items.append(cur)
            cur = None
            m = H3_RE.match(ln)
            if m:
                cur = {"title": re.sub(r"^\d+[.)]\s*", "", m.group(1)).strip(),
                       "positions": [], "prose": []}
            continue
        if cur is None:
            continue
        if not code and BULLET_RE.match(ln):
            close_block()
            block = [ln]
        elif block is not None and ln.strip() and not code and ln[:1] in (" ", "\t"):
            block.append(ln.strip())         # only an indented line continues a bullet
        else:
            close_block()
            if ln.strip():
                cur["prose"].append(ln)
    close_block()
    if cur:
        items.append(cur)
    out = []
    for it in items:
        side_set = {s.lower() for sides, _c in it["positions"] for s in sides}
        topics = [t for t in dict.fromkeys(links_outside_code("\n".join(it["prose"])))
                  if t.lower() not in side_set]
        out.append((it["title"], it["positions"], topics))
    return out


def is_dispute_hub(filename, text):
    name = filename[:-3] + " " + (page_title(text) or "")
    if not HUB_NAME_RE.search(name):
        return False
    return any(len(pos) >= 2 for _t, pos, _top in hub_items(text))


# ---------------------------------------------------------------------------
# Section edits
# ---------------------------------------------------------------------------
def add_bullets(text, wants, header, bullets, resolve, before="cites"):
    """Append bullets to the first section `wants(name)` accepts, creating `header`
    (placed before the first `before`-kind section, else at the end) if none exists.
    A bullet whose leading link already appears in that section is skipped, which is
    what makes normalization idempotent."""
    fm, start, lines = split_frontmatter(text)
    spans = h2_spans(lines, start)
    target = next((s for s in spans if wants(s[2])), None)
    present = set()
    if target:
        present = {resolve(t) for t in links_outside_code("\n".join(lines[target[0]:target[1]]))}
    fresh = []
    for b in bullets:
        m = LINK_RE.search(b)
        key = resolve(m.group(1)) if m else b
        if key in present:
            continue
        present.add(key)
        fresh.append(b)
    if not fresh:
        return text, 0
    if target:
        end = target[1]
        while end > target[0] + 1 and not lines[end - 1].strip():
            end -= 1
        new = lines[:end] + fresh + lines[end:]
    else:
        at = next((s[0] for s in spans if section_kind(s[2]) == before), None)
        block = ["## " + header, ""] + fresh + [""]
        if at is None:
            while lines and not lines[-1].strip():
                lines.pop()
            new = lines + [""] + block
        else:
            new = lines[:at] + block + lines[at:]
    return "\n".join(new), len(fresh)


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------
def _title_from_stem(stem):
    t = stem if " " in stem else re.sub(r"[-_]+", " ", stem)
    return t[:1].upper() + t[1:]


def normalize_texts(pages):
    """{filename: markdown} -> ({filename: markdown}, report). Pure and deterministic."""
    pages = dict(pages)
    rep = {"hub_renamed": None, "types_from_type_line": 0, "kinds_defaulted": [],
           "unrecognized_types": [], "sources_detected": [], "titles_added": [],
           "sources_synthesized": 0, "dispute_hubs": [], "disputes_placed": 0,
           "disputed_claims_listed": 0}

    lower = {fn.lower(): fn for fn in pages}
    if "index.md" not in lower and "readme.md" in lower:
        old = lower["readme.md"]
        pages["index.md"] = pages.pop(old)
        rep["hub_renamed"] = "%s -> index.md" % old

    alias = {}
    for fn in sorted(pages):
        alias.setdefault(fn[:-3].lower(), fn)
    for fn in sorted(pages):
        t = page_title(pages[fn])
        if t:
            alias.setdefault(t.lower(), fn)

    def resolve(target):
        return alias.get((target or "").strip().lower())

    hubs = {fn for fn in sorted(pages) if fn.lower() not in ("index.md", "log.md")
            and is_dispute_hub(fn, pages[fn])}

    # -- types, kinds, locators, titles -----------------------------------------
    ptype, locator = {}, {}
    for fn in sorted(pages):
        stem = fn[:-3]
        text = pages[fn]
        if stem.lower() in ("index", "log"):
            ptype[fn] = stem.lower()
            continue
        fm = split_frontmatter(text)[0] or {}
        pre = preamble(text)
        declared = (fm.get("type") or "").lower() or None
        updates = {}
        tl = TYPE_LINE_RE.search(pre)
        field = META_FIELD_RE.search(pre)
        if fn in hubs and not declared:
            declared = updates["type"] = "index"
        if not declared and "kind" not in fm:
            if tl:
                cls, val = classify_type(tl.group(1))
                rep["types_from_type_line"] += 1
                if cls == "source":
                    declared = updates["type"] = "source"
                    if val:
                        updates["medium"] = val
                elif cls == "concept":
                    updates["kind"] = val
                else:
                    updates["kind"] = "concept"
                    rep["unrecognized_types"].append("%s (%s)" % (fn, tl.group(1)))
            elif field and locator_in(field.group(1)):
                declared = updates["type"] = "source"
            else:
                updates["kind"] = "concept"
                rep["kinds_defaulted"].append(fn)
        if declared == "source":
            loc = fm.get("locator")
            if not loc:
                loc = (locator_in(field.group(1)) if field else None) or \
                      (locator_in(tl.group(1)) if tl else None)
                if loc:
                    updates["locator"] = loc
            if loc and "medium" not in fm and "medium" not in updates and medium_for(loc):
                updates["medium"] = medium_for(loc)
            locator[fn] = loc
            if "type" in updates:
                rep["sources_detected"].append(fn)
        ptype[fn] = declared or "concept"
        if updates:
            text = set_frontmatter(text, updates)
        if page_title(text) is None:
            fm2, start, lines = split_frontmatter(text)
            at = start
            while at < len(lines) and not lines[at].strip():
                at += 1
            lines[at:at] = ["# " + _title_from_stem(stem), ""]
            text = "\n".join(lines)
            rep["titles_added"].append(fn)
        pages[fn] = text
    for fn in sorted(pages):
        if fn in hubs and fn not in ptype:
            ptype[fn] = "index"

    # -- Sources from the source pages a concept links to -----------------------
    # (before disputes are distributed, so it reflects only what the author wrote)
    for fn in sorted(pages):
        if ptype.get(fn) != "concept":
            continue
        text = pages[fn]
        fm, start, lines = split_frontmatter(text)
        if any(section_kind(name) == "cites" for _h, _e, name in h2_spans(lines, start)):
            continue
        cited = []
        for tgt in links_outside_code("\n".join(lines[start:])):
            f = resolve(tgt)
            if f and ptype.get(f) == "source" and f not in cited:
                cited.append(f)
        if not cited:
            continue
        bullets = ["- %s — %s" % (locator[f], page_title(pages[f]) or f[:-3])
                   if locator.get(f) else "- [[%s]]" % f[:-3] for f in cited]
        while lines and not lines[-1].strip():
            lines.pop()
        pages[fn] = "\n".join(lines + ["", "## Sources", ""] + bullets) + "\n"
        rep["sources_synthesized"] += 1

    # -- Contradictions hubs ----------------------------------------------------
    for hub in sorted(hubs):
        rep["dispute_hubs"].append(hub)
        for title, positions, topics in hub_items(pages[hub]):
            if len(positions) < 2:
                continue
            for i, (sides_i, _claim_i) in enumerate(positions):
                for j, (sides_j, claim_j) in enumerate(positions):
                    if i == j:
                        continue
                    for a in sides_i:
                        fa = resolve(a)
                        if not fa or fa == hub:
                            continue
                        bullets = ["- [[%s]] — %s: %s" % (b, title, claim_j)
                                   for b in sides_j if resolve(b) and resolve(b) not in (fa, hub)]
                        pages[fa], n = add_bullets(
                            pages[fa], lambda s: section_kind(s) == "contradicts",
                            "Contradictions / tensions", bullets, resolve)
                        rep["disputes_placed"] += n
            side_files = {resolve(s) for sides, _c in positions for s in sides}
            for topic in topics:
                ft = resolve(topic)
                if not ft or ft == hub or ft in side_files:
                    continue
                bullets = ["- [[%s]] — %s: %s" % (s, title, claim)
                           for sides, claim in positions for s in sides if resolve(s)]
                pages[ft], n = add_bullets(
                    pages[ft], lambda s: s.strip().lower() == "disputed claims",
                    "Disputed claims", bullets, resolve)
                rep["disputed_claims_listed"] += n
    return pages, rep


def read_wiki(src_dir):
    out = {}
    for f in sorted(glob.glob(os.path.join(src_dir, "*.md"))):
        with open(f, encoding="utf-8") as fh:
            out[os.path.basename(f)] = fh.read()
    return out


def normalize_wiki(src_dir, dst_dir):
    """Write a normalized copy of src_dir into dst_dir (which must be empty)."""
    if os.path.isdir(dst_dir) and os.listdir(dst_dir):
        raise ValueError("normalized output directory is not empty: %s" % dst_dir)
    os.makedirs(dst_dir, exist_ok=True)
    pages, rep = normalize_texts(read_wiki(src_dir))
    for fn, text in pages.items():
        with open(os.path.join(dst_dir, fn), "w", encoding="utf-8") as fh:
            fh.write(text)
    return rep


def report_lines(rep):
    """Human summary of what normalization did; empty when the wiki needed nothing."""
    out = []
    if rep["hub_renamed"]:
        out.append("hub %s" % rep["hub_renamed"])
    if rep["types_from_type_line"]:
        out.append("%d page type(s) read from **Type:** lines" % rep["types_from_type_line"])
    if rep["sources_detected"]:
        out.append("%d page(s) recognised as sources (artifacts, not concepts)"
                   % len(rep["sources_detected"]))
    if rep["sources_synthesized"]:
        out.append("%d page(s) given a Sources section from the source pages they link"
                   % rep["sources_synthesized"])
    if rep["dispute_hubs"]:
        out.append("%d contradictions hub(s) distributed: %d contradiction(s) placed on the "
                   "pages that disagree, %d disputed claim(s) listed on their topics"
                   % (len(rep["dispute_hubs"]), rep["disputes_placed"],
                      rep["disputed_claims_listed"]))
    if rep["titles_added"]:
        out.append("%d title(s) added from filenames" % len(rep["titles_added"]))
    if rep["kinds_defaulted"]:
        out.append("%d page(s) with no type information defaulted to kind: concept"
                   % len(rep["kinds_defaulted"]))
    if rep["unrecognized_types"]:
        out.append("%d **Type:** value(s) not recognised, defaulted to concept: %s"
                   % (len(rep["unrecognized_types"]), ", ".join(rep["unrecognized_types"][:3])))
    return out
