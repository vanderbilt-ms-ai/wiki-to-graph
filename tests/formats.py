"""Render one wiki's content in the other shapes LLM wikis are commonly written in.

test_convergence builds every rendering and asserts the graph has the same structure
as the original. That is the whole guarantee this package makes about format: the
same content produces the same graph, whatever shape it was written in.
"""
import re

LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
BULLET_RE = re.compile(r"^\s*[-*+]\s+")
LEAD_RE = re.compile(r"^\s*[-*+]\s+\[\[([^\]|]+)(?:\|[^\]]*)?\]\]\s*—\s*(.*)$")

KIND_WORD = {"concept": "concept", "schema": "architecture",
             "procedure": "method", "fact": "phenomenon"}


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def split_frontmatter(text):
    if text.startswith("---\n"):
        end = text.index("\n---", 3)
        fm = dict(re.findall(r"^(\w+):\s*(.*?)\s*$", text[4:end], re.M))
        return fm, text[end + 4:].lstrip("\n")
    return {}, text


def split_sections(body):
    """-> (head, [(name, content)]) where head is everything before the first '## '."""
    parts = re.split(r"^## (.+)$", body, flags=re.M)
    head, rest = parts[0], parts[1:]
    return head, [(rest[i].strip(), rest[i + 1]) for i in range(0, len(rest), 2)]


def join_sections(head, secs):
    return head.rstrip("\n") + "\n\n" + "\n".join(
        "## %s\n%s" % (name, content if content.endswith("\n") else content + "\n")
        for name, content in secs)


def bullets(content):
    """Logical bullets (continuation lines joined)."""
    out = []
    for line in content.splitlines():
        if BULLET_RE.match(line):
            out.append(line.rstrip())
        elif line.strip() and out:
            out[-1] += " " + line.strip()
    return out


def is_concept(fm):
    return fm.get("type", "concept") == "concept"


def render_flat(pages):
    """A wiki grown by hand: kebab-case filenames, a README hub, '**Type:**' lines in
    place of frontmatter, papers described in a metadata line, bare bullet lists of
    related links, disagreements as prose paragraphs under renamed headings, and no
    Sources sections — the source pages are linked from the text instead."""
    rename = {fn[:-3]: slug(fn[:-3]) for fn in pages if fn not in ("index.md", "log.md")}

    def relink(text):
        return LINK_RE.sub(lambda m: "[[%s%s]]" % (
            rename.get(m.group(1).strip(), m.group(1).strip()),
            "|" + m.group(2) if m.group(2) else ""), text)

    out = {}
    for fn, text in pages.items():
        if fn == "index.md":
            out["README.md"] = relink(text)
            continue
        if fn == "log.md":
            out[fn] = relink(text)
            continue
        fm, body = split_frontmatter(text)
        head, secs = split_sections(body)
        meta = ("**Type:** paper · **File:** `%s`" % fm["locator"]
                if fm.get("type") == "source" else "**Type:** %s" % KIND_WORD[fm["kind"]])
        head = re.sub(r"^(# .+)$", lambda m: m.group(1) + "\n\n" + meta, head, count=1, flags=re.M)
        new = []
        for name, content in secs:
            if name == "Sources" and is_concept(fm):
                continue
            if name == "Related":
                links = [LEAD_RE.match(b).group(1) for b in bullets(content) if LEAD_RE.match(b)]
                new.append(("See also", "\n- " + " · ".join("[[%s]]" % x for x in links) + "\n"))
            elif name == "Contradictions / tensions":
                paras = [BULLET_RE.sub("", b) for b in bullets(content)] or [content.strip()]
                new.append(("Tensions", "\n" + "\n\n".join(paras) + "\n"))
            elif name == "Summary":
                new.append(("Overview", content))
            elif name == "Explanation":
                new.append(("Details", content))
            else:
                new.append((name, content))
        out[rename[fn[:-3]] + ".md"] = relink(join_sections(head, new))
    return out


def render_vault(pages):
    """An Obsidian-style vault: frontmatter kinds, a single bare line of related links,
    disagreement bullets led by a bold label, every citation on one line."""
    out = {}
    for fn, text in pages.items():
        if fn in ("index.md", "log.md"):
            out[fn] = text
            continue
        fm, body = split_frontmatter(text)
        front = text[: len(text) - len(body)]
        head, secs = split_sections(body)
        new = []
        for name, content in secs:
            bs = bullets(content)
            if name == "Related":
                links = [LEAD_RE.match(b).group(1) for b in bs if LEAD_RE.match(b)]
                new.append((name, " · ".join("[[%s]]" % x for x in links) + "\n"))
            elif name == "Contradictions / tensions" and any(LEAD_RE.match(b) for b in bs):
                new.append((name, "\n".join(
                    "- **vs [[%s]]:** %s" % LEAD_RE.match(b).groups() if LEAD_RE.match(b) else b
                    for b in bs) + "\n"))
            elif name == "Sources" and len(bs) > 1:
                new.append((name, "- " + "; ".join(BULLET_RE.sub("", b) for b in bs) + "\n"))
            else:
                new.append((name, content))
        out[fn] = front + join_sections(head, new)
    return out


def render_hub(pages):
    """Every disagreement moved off the pages that disagree onto one contradictions
    page, written as '### item' headings with '- [[side]]: claim' bullets."""
    out, items = {}, []
    for fn in sorted(pages):
        text = pages[fn]
        if fn in ("index.md", "log.md"):
            out[fn] = text
            continue
        fm, body = split_frontmatter(text)
        front = text[: len(text) - len(body)]
        head, secs = split_sections(body)
        title = re.search(r"^# (.+)$", head, re.M).group(1)
        kept = []
        for name, content in secs:
            if name == "Contradictions / tensions":
                for b in bullets(content):
                    m = LEAD_RE.match(b)
                    if m:
                        items.append((title, fn[:-3], m.group(1), m.group(2)))
                continue
            kept.append((name, content))
        out[fn] = front + join_sections(head, kept)
    hub = ["# Contradictions", "", "Disagreements across the sources.", "", "## Disagreements", ""]
    for title, a, b, claim in items:
        hub += ["### %s vs %s" % (title, b), "", "- [[%s]]: %s" % (a, claim),
                "- [[%s]]: %s" % (b, claim), ""]
    out["Contradictions.md"] = "\n".join(hub)
    return out


STYLES = {"flat": render_flat, "vault": render_vault, "hub": render_hub}
