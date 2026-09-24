#!/usr/bin/env python3
"""
Build the Quartz content folder from the Obsidian vault.

    python3 .site-build/build_site.py . quartz/content      (run from the vault folder)

What it does, so the published pages read like the Obsidian ones:
  * Overview pages (📍 …) have every ![[embed]] replaced by the embedded note's text,
    recursively, with heading levels shifted to sit under the heading they follow.
    The result is one long page whose table of contents lists every heading.
  * ```base blocks become static markdown tables.
  * ```datacorejsx CovalonEntries blocks become one heading per entry, followed by the
    entry's properties and its full text.
  * Each note's own properties are shown as a list at the top of its page.
  * Images with alt text become <figure> elements with a caption.
  * Emoji prefixes are dropped from file and folder names, and every wikilink is
    rewritten to the note's full path in the output so links never resolve ambiguously.
"""
import html, re
import sys
import shutil
import pathlib

import yaml

SRC = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent.parent)
OUT = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "quartz/content")
SKIP_FOLDERS = {"🔑 Setup"}   # Obsidian-only notes, never published
HIDDEN_PROPS = {"tags", "aliases", "cssclasses"}
PREFIX = re.compile(r"^(?:📍|📄)\s*")


# ------------------------------------------------------------------ loading
class Note:
    def __init__(self, path: pathlib.Path):
        self.path = path
        self.name = path.stem
        text = path.read_text(encoding="utf-8")
        m = re.match(r"---\n(.*?)\n---\n?", text, re.S)
        self.props = (yaml.safe_load(m.group(1)) or {}) if m else {}
        self.body = text[m.end():] if m else text
        rel = path.relative_to(SRC)
        parts = [PREFIX.sub("", p) for p in rel.parts]
        parts[-1] = parts[-1][:-3]  # drop .md
        self.out_rel = "/".join(parts)  # e.g. "Player's Guide/Chapter 1 - Player Expectations/Community Guidelines"
        self.title = PREFIX.sub("", self.name)

    def prop(self, key, default=None):
        for k, v in self.props.items():
            if k.lower() == key.lower():
                return v
        return default

    @property
    def tags(self):
        t = self.prop("tags") or []
        return [t] if isinstance(t, str) else list(t)


notes = {}
for p in sorted(SRC.rglob("*.md")):
    if any(part.startswith(".") for part in p.relative_to(SRC).parts) or p.relative_to(SRC).parts[0] in SKIP_FOLDERS:   # .obsidian, .site-build, 🔑 Setup
        continue
    n = Note(p)
    notes[n.name] = n


# ------------------------------------------------------------------ helpers
def value_text(v):
    if v is None:
        return ""
    if isinstance(v, list):
        return ", ".join(value_text(x) for x in v)
    return str(v)


def plain(v):
    """Sort key: strip link syntax so [[Heart's Forest]] sorts as Heart's Forest."""
    s = value_text(v)
    s = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    return s.casefold()


def district_of(note):
    raw = value_text(note.prop("district", ""))
    m = (re.search(r"\[\[[^\]#|]*#([^\]|]+)", raw) or re.search(r"\[\[[^\]|]*\|([^\]]+)\]\]", raw)
         or re.search(r"\[\[([^\]|#]+)\]\]", raw))
    return (m.group(1) if m else raw).strip()


def props_list(note, hide=()):
    hide = {h.lower() for h in hide}
    rows = []
    for k, v in note.props.items():
        if k.lower() in HIDDEN_PROPS or k.lower() in hide or v in (None, "", []):
            continue
        rows.append(f"- **{k}:** {value_text(v)}")
    return "\n".join(rows)


HEADING = re.compile(r"(?m)^((?:> ?)*)(#{1,6})(\s)")


def shift_to(text, target):
    """Shift headings so the shallowest non-callout heading becomes `target`."""
    levels = [len(m.group(2)) for m in HEADING.finditer(text) if not m.group(1)]
    if not levels:
        return text
    delta = target - min(levels)
    if delta == 0:
        return text
    return HEADING.sub(lambda m: m.group(1) + "#" * max(1, min(6, len(m.group(2)) + delta)) + m.group(3), text)


def last_heading_level(text):
    levels = [len(m.group(2)) for m in HEADING.finditer(text) if not m.group(1)]
    return levels[-1] if levels else 0


def section_of(note, heading):
    """Text under a heading of a note (for ![[Note#Heading]] embeds)."""
    lines = note.body.split("\n")
    out, level = None, None
    for line in lines:
        m = re.match(r"(#{1,6})\s+(.*?)\s*$", line)
        if out is None:
            if m and m.group(2) == heading:
                out, level = [line], len(m.group(1))
            continue
        if m and len(m.group(1)) <= level:
            break
        out.append(line)
    return "\n".join(out or [])


# ------------------------------------------------------------------ Bases -> tables
def tagged(tag):
    return [n for n in notes.values() if tag in n.tags]


def render_base(src):
    spec = yaml.safe_load(src) or {}
    filters = (spec.get("filters") or {}).get("and", [])
    rows = list(notes.values())
    for f in filters:
        f = str(f)
        m = re.match(r'file\.hasTag\("([^"]+)"\)', f)
        if m:
            rows = [n for n in rows if m.group(1) in n.tags]
            continue
        m = re.match(r'(\w[\w ]*?)\s*==\s*"([^"]+)"', f)
        if m:
            key, val = m.group(1), m.group(2)
            rows = [n for n in rows if (district_of(n) if key.lower() == "district" else plain(n.prop(key))) in (val, val.casefold())]
    names = {k: (v or {}).get("displayName", k) for k, v in (spec.get("properties") or {}).items()}
    out = []
    for view in spec.get("views", []):
        cols = view.get("order", ["file.name"])
        view_rows = rows[:]
        for s in reversed(view.get("sort", [])):
            key = s["property"]
            if key.startswith("formula."):
                expr = str((spec.get("formulas") or {}).get(key[8:], ""))
                src = "file.name" if expr.startswith("file.name") else expr.split(".")[0]
                strip_the = "/^the /i" in expr
            else:
                src, strip_the = key, False
            def keyf(n, src=src, strip_the=strip_the):
                v = n.name if src == "file.name" else plain(n.prop(src))
                return (re.sub(r"^the ", "", v, flags=re.I) if strip_the else v).casefold()
            view_rows.sort(key=keyf, reverse=s.get("direction", "ASC") == "DESC")
        head = ["Name" if c == "file.name" else names.get(c, c) for c in cols]
        out.append("| " + " | ".join(head) + " |")
        out.append("| " + " | ".join(":--" for _ in cols) + " |")
        for n in view_rows:
            cells = []
            for c in cols:
                cell = f"[[{n.name}]]" if c == "file.name" else value_text(n.prop(c))
                cells.append(cell.replace("\n", " "))
            out.append("| " + " | ".join(cells) + " |")
        out.append("")
    # on the site these tables get a filter box, a drop-down per short column and click-to-sort headers
    return '<div class="covalon-filterable">\n\n' + "\n".join(out) + '\n\n</div>\n'


# ------------------------------------------------------------------ Datacore CovalonEntries -> headings
def jsx_prop(src, key):
    m = re.search(rf'{key}="([^"]*)"', src)
    if m:
        return m.group(1)
    m = re.search(rf"{key}=\{{\[([^\]]*)\]\}}", src)
    if m:
        return re.findall(r'"([^"]*)"', m.group(1))
    return None


MISSION = re.compile(r"^### Mission ([A-Z])(?::\s*(.+?))?\s*$")


def render_missions():
    """<MissionOverview />: every expedition's missions (from their ## Missions sections) as one table."""
    rows = ["| Expedition | Mission | Summary |", "| :-- | :-- | :-- |"]
    exps = sorted(tagged("covalon/expedition"), key=lambda n: plain(n.prop("Journey Date")))
    for n in exps:
        in_missions, cur, missions = False, None, []
        for line in n.body.split("\n"):
            if line.startswith("## "):
                in_missions, cur = line.strip() == "## Missions", None
                continue
            if not in_missions:
                continue
            m = MISSION.match(line)
            if m:
                cur = [m.group(1), (m.group(2) or "").strip(), []]
                missions.append(cur)
            elif re.match(r"^#{1,3} ", line):
                cur = None
            elif cur:
                cur[2].append(line.strip())
        for i, (letter, name, text) in enumerate(missions):
            place = f"[[{n.name}|{n.name.removesuffix(' Expedition')}]]"   # on every row, so the filter box keeps whole expeditions
            anchor = f"Mission {letter} {name}".strip()
            label = f"{letter}: {name}" if name else letter
            summary = "<br>".join(t for t in text if t).replace("|", "\\|")   # paragraphs on their own lines
            rows.append(f"| {place} | [[{n.name}#{anchor}\\|{label}]] | {summary} |")
    return '<div class="covalon-filterable">\n\n' + "\n".join(rows) + '\n\n</div>\n'


def render_entries(src, stack):
    if "MissionOverview" in src:
        return render_missions()
    tag = jsx_prop(src, "tag")
    if not tag:
        return ""
    district = jsx_prop(src, "district")
    sort_by = jsx_prop(src, "sortBy") or "name"
    level = int((jsx_prop(src, "heading") or "h2")[1])
    hide = jsx_prop(src, "hide") or []
    entries = tagged(tag)
    if district:
        entries = [n for n in entries if district_of(n) == district]
    sort_prop = "date" if sort_by == "date" else sort_by
    if sort_by == "name":
        keyf = lambda n: n.name.casefold()
    elif sort_by == "title":
        keyf = lambda n: re.sub(r"^the ", "", n.name, flags=re.I).casefold()
    else:
        keyf = lambda n: plain(n.prop(sort_prop))
    entries.sort(key=keyf)
    out = []
    for n in entries:
        out.append(f"{'#' * level} [[{n.name}]]")
        props = props_list(n, hide)
        if props:
            out.append(props)
        body = render(n, stack)
        out.append(shift_to(body, level + 1))
    return "\n\n".join(out)


# ------------------------------------------------------------------ embeds
EMBED = re.compile(r"(?m)^[ \t]*!\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\|[^\]]*)?\]\][ \t]*$")
CODE = re.compile(r"```(base|datacorejsx)\n(.*?)\n```", re.S)


def render(note, stack=()):
    if note.name in stack:
        return f"*(embed loop: {note.name})*"
    stack = stack + (note.name,)
    text = note.body
    text = CODE.sub(lambda m: render_base(m.group(2)) if m.group(1) == "base" else render_entries(m.group(2), stack), text)

    out, pos = [], 0
    for m in EMBED.finditer(text):
        before = text[pos:m.start()]
        out.append(before)
        target = notes.get(m.group(1))
        if not target:
            out.append(m.group(0))
        else:
            inner = section_of(target, m.group(2)) if m.group(2) else render(target, stack)
            level = last_heading_level("".join(out))
            inner = shift_to(inner.strip(), level + 1) if level else inner.strip()
            classes = target.prop("cssclasses") or []
            classes = [classes] if isinstance(classes, str) else list(classes)
            if classes and not m.group(2):   # keep the embedded note's cssclasses (e.g. even-columns)
                inner = f'<div class="{" ".join(classes)}">\n\n{inner}\n\n</div>'
            out.append(inner)
        pos = m.end()
    out.append(text[pos:])
    return "".join(out).strip() + "\n"


# ------------------------------------------------------------------ output rewriting
def rewrite_links(text):
    def link(m, in_table):
        target, heading, alias = m.group(2), m.group(3) or "", m.group(4)
        n = notes.get(target.replace("''", "'"))
        if not n:
            return m.group(0)
        label = alias if alias is not None else (n.title if n.title != n.out_rel else None)
        sep = "\\|" if in_table else "|"
        return f"{m.group(1)}[[{n.out_rel}{heading}{sep + label if label else ''}]]"

    lines = []
    for line in text.split("\n"):
        in_table = line.lstrip("> ").startswith("|")
        lines.append(re.sub(r"(!?)\[\[([^\]|#\\]+)(#[^\]|\\]*)?(?:\\?\|([^\]]*))?\]\]",
                            lambda m: link(m, in_table), line))
    return "\n".join(lines)


def figures(text):
    def fig(m):
        alt, width, url = m.group(1), m.group(2), m.group(3)
        w = f' width="{width}"' if width else ""
        img = f'<img src="{url}" alt="{alt}"{w} loading="lazy">'
        return f"<figure>{img}<figcaption>{alt}</figcaption></figure>" if alt else img
    return re.sub(r"!\[([^\]|]*)(?:\|(\d+))?\]\(([^)\s]+)\)", fig, text)


# ------------------------------------------------------------------ chapter navigation
GUIDES = ["📍 Covalon Player's Guide", "📍 Covalon GM's Guide"]
CHAPTER = re.compile(r"(?m)^# (.+)\n+!\[\[([^\]|#]+)\]\]")
NAV = {}  # chapter note name -> (guide note name, [(heading, chapter note name), ...], index)
for g in GUIDES:
    if g in notes:
        chapters = [(m.group(1).strip(), m.group(2)) for m in CHAPTER.finditer(notes[g].body)]
        for i, (_, target) in enumerate(chapters):
            NAV[target] = (g, chapters, i)
        # on the big page, offer each chapter as its own page too
        notes[g].body = CHAPTER.sub(
            lambda m: f"# {m.group(1)}\n\n*[[{m.group(2)}|Read this chapter on its own page →]]*\n\n![[{m.group(2)}]]",
            notes[g].body)


def chapter_nav(name):
    guide, chapters, i = NAV[name]
    prev = f"[[{chapters[i-1][1]}|← {chapters[i-1][0]}]]" if i > 0 else ""
    here = f"[[{guide}#{chapters[i][0]}|{chapters[i][0]}]]"
    nxt = f"[[{chapters[i+1][1]}|{chapters[i+1][0]} →]]" if i + 1 < len(chapters) else ""
    return (f'<span class="chapter-nav" data-pagefind-ignore><span class="prev">{prev}</span>'
            f'<span class="current">{here}</span><span class="next">{nxt}</span></span>')


# ------------------------------------------------------------------ Pagefind (site search with filters)
# Each page is marked up for Pagefind: its text is indexed, and its short properties become search filters.
TYPES = {"Deities": "Deity", "Guilds": "Guild", "Locations": "Location", "Civilizations": "Civilization",
         "Expeditions": "Expedition", "Campaign Events": "Campaign Event", "Adventure Types": "Adventure Type"}
# Properties left out of the search filters: long text, dates, and lists too long to be useful as filters
NOT_FILTERS = {"order", "description", "tagline", "expedition summary", "roleplay channel",
               "edicts", "anathema", "membership requirements", "goals", "values", "date", "journey date",
               "finale first cleared", "population", "created by", "cleric spells", "members", "leader",
               "pantheon members", "guild headquarters of", "primary exports", "finale", "fate"}


def page_type(note):
    top = note.path.relative_to(SRC).parts[0]
    if top.startswith("📄"):
        return "Table" if note.name.startswith("Table ") else PREFIX.sub("", top)
    return TYPES.get(top, top)


def search_markup(note):
    esc = lambda t: html.escape(str(t), quote=True)
    tags = [f'<span hidden data-pagefind-meta="title">{esc(note.title)}</span>',
            f'<span hidden data-pagefind-filter="Type">{esc(page_type(note))}</span>']
    for k, v in note.props.items():
        if k.lower() in HIDDEN_PROPS or k.lower() in NOT_FILTERS or v in (None, "", []):
            continue
        values = [plain_case(x) for x in (v if isinstance(v, list) else [v])]
        if not all(0 < len(x) <= 40 for x in values):   # long text makes a poor filter
            continue
        tags += [f'<span hidden data-pagefind-filter="{esc(k)}">{esc(x)}</span>' for x in values]
    return "".join(tags)


def plain_case(v):
    s = value_text(v)
    s = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", s)
    return re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s).strip()


def write_page(note):
    body = render(note)
    classes = note.prop("cssclasses") or []
    classes = [classes] if isinstance(classes, str) else list(classes)
    if classes:   # the note's cssclasses (e.g. even-columns) apply to its own page too
        body = f'<div class="{" ".join(classes)}">\n\n{body.strip()}\n\n</div>\n'
    props = props_list(note)
    if props:
        body = props + "\n\n" + body
    if note.name in NAV:
        nav = chapter_nav(note.name)
        body = nav + "\n\n" + body.strip() + "\n\n" + nav + "\n"
    body = figures(rewrite_links(body))
    if not note.name.startswith("📍"):   # overview pages repeat their entries' text, so leave them out of search
        body = f'<div data-pagefind-body>\n\n{search_markup(note)}\n\n{body.strip()}\n\n</div>\n'
    fm = {"title": NAV[note.name][1][NAV[note.name][2]][0] if note.name in NAV else note.title}
    tags = [t.lower() for t in note.tags]
    if tags:
        fm["tags"] = tags
    aliases = note.prop("aliases")
    if aliases:
        fm["aliases"] = aliases
    dest = OUT / f"{note.out_rel}.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("---\n" + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False).strip() + "\n---\n\n" + body, encoding="utf-8")


HOME = """---
title: Covalon
---

Welcome to the Covalon guides: everything you need to play in, or run games for, Covalon, a Pathfinder 2nd Edition living world campaign.

## The guides

- [[{player}|Covalon Player's Guide]]: the full player's guide on one page.
- [[{gm}|Covalon GM's Guide]]: the full guide for Dungeon Guides on one page.
- [[{types}|Adventure Types]]: every kind of adventure Covalon runs.
- [[search|Advanced search]]: search every page, filtered by type and properties (deity domains, soul seeds, districts and more).

## The world

- [[{gaz}|Covalon Gazetteer]]
- [[{guilds}|Guilds]]
- [[{civs}|Pre-Cataclysm Civilizations]]
- [[{exps}|Expeditions]]
- [[{deities}|Deities, Faith, and Ideologies]]
- [[{events}|Campaign Events]]
"""

SEARCH = """---
title: Advanced Search
---

Search every page of the guides. Use the filters to narrow the results by page type or by properties such as a deity's domains, an expedition's soul seed or a location's district.
"""


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for n in notes.values():
        write_page(n)
    p = lambda name: notes[name].out_rel
    (OUT / "index.md").write_text(HOME.format(
        player=p("📍 Covalon Player's Guide"), gm=p("📍 Covalon GM's Guide"),
        gaz=p("📍 Covalon Gazetteer"), guilds=p("📍 Guilds"), civs=p("📍 Pre-Cataclysm Civilizations"),
        exps=p("📍 Expeditions"), types=p("📍 Adventure Types"), deities=p("📍 Deities, Faith, and Ideologies"), events=p("📍 Campaign Events"),
    ), encoding="utf-8")
    (OUT / "search.md").write_text(SEARCH, encoding="utf-8")
    print(f"wrote {len(notes) + 2} pages to {OUT}")


if __name__ == "__main__":
    main()
