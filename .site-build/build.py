#!/usr/bin/env python3
"""
Build the Covalon website from this Obsidian vault.

    python3 .site-build/build.py [vault] [output]        (defaults: the vault this folder is in, ./public)

The site is plain HTML written with the same page structure and class names Obsidian uses in reading
view, so the vault's own CSS snippets (.obsidian/snippets, the ones switched on in Appearance) style
the site directly. assets/base.css stands in for Obsidian's built-in theme, and assets/site.css adds
the site's frame: sidebar with the file tree, table of contents, search and light/dark switch.

What the build does with the notes:
  * Overview pages (📍 …) have every ![[embed]] replaced by the embedded note, recursively, with
    heading levels shifted to sit under the heading they follow: one long page.
  * ```base blocks become tables (with a filter box on the site); ```datacorejsx blocks become the
    same entries / tables the Datacore components draw in Obsidian.
  * Callouts get Obsidian's markup, with the colours and icons set in Callout Manager.
  * Each page's properties are shown in a panel at the top.
  * Pages are marked up for Pagefind, the search index built afterwards (see build-local.sh).
"""
import datetime
import unicodedata
import html
import io
import json
import os
import pathlib
import re
import shutil
import sys
import tarfile
import urllib.request
from urllib.parse import quote

import yaml
from bs4 import BeautifulSoup, NavigableString, Tag
from markdown_it import MarkdownIt
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.tasklists import tasklists_plugin

HERE = pathlib.Path(__file__).resolve().parent
SRC = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE.parent
OUT = pathlib.Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else pathlib.Path("public").resolve()
SITE_TITLE = "Covalon"
SKIP_FOLDERS = {"🔑 Setup"}   # Obsidian-only notes, never published
HIDDEN_PROPS = {"tags", "aliases", "cssclasses"}
PREFIX = re.compile(r"^(?:📍|📄)\s*")
FIRST = ["Player's Guide", "GM's Guide"]   # shown first in the sidebar, in this order


# ================================================================== notes
class Note:
    def __init__(self, path: pathlib.Path):
        self.path = path
        self.name = path.stem
        text = path.read_text(encoding="utf-8")
        m = re.match(r"---\n(.*?)\n---\n?", text, re.S)
        self.props = (yaml.safe_load(m.group(1)) or {}) if m else {}
        self.body = text[m.end():] if m else text
        rel = path.relative_to(SRC)
        self.folders = [PREFIX.sub("", p) for p in rel.parts[:-1]]
        self.title = PREFIX.sub("", self.name)
        # each page is a folder with an index.html, so its address has no .html: /Guilds/The-Archivists/
        page = slug(plain_letters(str(self.props.get("_url") or ""))).lower().strip("-") if self.props.get("_url") else ""
        page = page or slug(plain_letters(self.title)).lower()
        if self.folders and self.folders[-1] == "Expeditions":   # /expeditions/alatar/, not /expeditions/alatar-expedition/
            page = page.removesuffix("-expedition") or page
        m = re.match(r"Table (\d+-\d+)\b", self.title)
        if m and self.folders and self.folders[-1] == "Tables":   # /players/table/3-2/
            page = m.group(1)
        self.url = "/".join([url_part(p) for p in self.folders] + [page]) + "/index.html"

    def prop(self, key, default=None):
        for k, v in self.props.items():
            if k.lower() == key.lower():
                return v
        return default

    @property
    def tags(self):
        t = self.prop("tags") or []
        return [t] if isinstance(t, str) else list(t)

    @property
    def classes(self):
        c = self.prop("cssclasses") or []
        return [c] if isinstance(c, str) else list(c)


def slug(text):
    """File and anchor names: letters and digits kept (any language), everything else becomes '-'."""
    return re.sub(r"[^\w]+", "-", text).strip("-") or "page"


# Short addresses for some folders and pages; every other folder and page is its name in lower case,
# with plain letters for accented ones (/guilds/the-archivists/, /civilizations/pudersno/)
# A page can pick its own address with a `_url` property (e.g. `_url: briarmurk` on The Briarmurk).
FOLDER_URLS = {"Player's Guide": "players", "GM's Guide": "gms", "Tables": "table"}


def plain_letters(text):
    """ö → o, é → e and so on (letters with no plain form, e.g. in Chinese names, are kept)."""
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def url_part(name):
    return FOLDER_URLS.get(name) or slug(plain_letters(name)).lower()


def heading_slug(text):
    return slug(re.sub(r"[*_`~=]", "", text)).lower()


notes = {}
for p in sorted(SRC.rglob("*.md")):
    rel = p.relative_to(SRC)
    if any(part.startswith(".") for part in rel.parts) or rel.parts[0] in SKIP_FOLDERS:
        continue
    n = Note(p)
    notes[n.name] = n

# A folder's pinned overview (📍) is the folder's own page: /Guilds/ rather than /Guilds/Guilds/.
# With several pinned notes in a folder, the one named after the folder gets it (/Expeditions/), and the
# others keep their own address (/Expeditions/Mission-Overview/).
_pinned = {}
for n in notes.values():
    if n.name.startswith("📍") and n.folders:
        _pinned.setdefault(tuple(n.folders), []).append(n)
for folders, group in _pinned.items():
    main = group[0] if len(group) == 1 else next((n for n in group if n.title == folders[-1]), None)
    if main:
        main.url = "/".join(url_part(p) for p in folders) + "/index.html"

# pictures and other files kept in the vault (e.g. 🖼️ Assets), found by file name like Obsidian does
FILE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".avif", ".bmp", ".pdf"}
files = {}
for p in sorted(SRC.rglob("*")):
    rel = p.relative_to(SRC)
    if p.is_file() and p.suffix.lower() in FILE_EXT and not any(part.startswith(".") for part in rel.parts):
        files.setdefault(p.name.casefold(), p)
USED_FILES = {}   # vault file -> its path on the site; copied into the site when the pages are written


def file_url(name):
    p = files.get(name.strip().split("/")[-1].casefold())
    if not p:
        return None
    url = "files/" + "/".join(slug(PREFIX.sub("", part)) if i < len(p.relative_to(SRC).parts) - 1 else part
                              for i, part in enumerate(re.sub(r"^\W+\s*", "", x) or x for x in p.relative_to(SRC).parts))
    url = plain_letters(url).lower()   # addresses in lower case, pictures too (files/assets/covalon-logo….webp)
    USED_FILES[p] = url
    return url


lookup = {}   # every name a link can use: note name, title, aliases (case-insensitive)
for n in notes.values():
    aliases = n.prop("aliases") or []
    for key in [n.name, n.title] + ([aliases] if isinstance(aliases, str) else list(aliases)):
        lookup.setdefault(str(key).casefold(), n)


def find(target):
    target = target.strip().replace("''", "'")
    return notes.get(target) or lookup.get(target.casefold()) or lookup.get(target.split("/")[-1].casefold())


# ================================================================== helpers
def ordinal(n):
    return f"{n}{'th' if 11 <= n % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def nice_date(d):
    """Dates are shown as "July 17th, 2021"."""
    return f"{d:%B} {ordinal(d.day)}, {d.year}"


def value_text(v):
    if v is None:
        return ""
    if isinstance(v, list):
        return ", ".join(value_text(x) for x in v)
    if isinstance(v, datetime.date):
        return nice_date(v)
    return str(v)


def plain(v):
    """Sort key: link syntax stripped, so [[Heart's Forest]] sorts as Heart's Forest."""
    s = value_text(v)
    s = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    return s.casefold()


def plain_case(v):
    s = value_text(v)
    s = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", s)
    return re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s).strip()


def district_of(note):
    raw = value_text(note.prop("district", ""))
    m = (re.search(r"\[\[[^\]#|]*#([^\]|]+)", raw) or re.search(r"\[\[[^\]|]*\|([^\]]+)\]\]", raw)
         or re.search(r"\[\[([^\]|#]+)\]\]", raw))
    return (m.group(1) if m else raw).strip()


def tagged(tag):
    return [n for n in notes.values() if tag in n.tags]


def props_panel(note, hide=()):
    """The two-column properties panel (the vault's .covalon-props, same markup as the Datacore component)."""
    hide = {h.lower() for h in hide}
    rows = []
    for k, v in note.props.items():
        if k.lower() in HIDDEN_PROPS or k.startswith("_") or k.lower() in hide or v in (None, "", []):
            continue
        value = md.renderInline(inline_markdown(value_text(v)))
        rows.append(f'<div class="covalon-prop"><span class="covalon-prop-key">{html.escape(str(k))}</span>'
                    f' <span class="covalon-prop-value">{value}</span></div>')
    return f'<div class="covalon-props">{"".join(rows)}</div>' if rows else ""


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


def section_of(note, heading, keep_heading=False):
    """Text under a heading of a note (for ![[Note#Heading]] embeds); the heading line itself is dropped,
    as the vault's CSS hides it in these embeds."""
    out, level = None, None
    for line in note.body.split("\n"):
        m = re.match(r"(#{1,6})\s+(.*?)\s*$", line)
        if out is None:
            if m and m.group(2) == heading:
                out, level = ([line] if keep_heading else []), len(m.group(1))
            continue
        if m and len(m.group(1)) <= level:
            break
        out.append(line)
    return "\n".join(out or [])


# ================================================================== Bases -> tables
def base_cell(n, col, spec):
    if col.startswith("formula."):   # the formulas the vault uses: a date property shown with .format(...)
        expr = str((spec.get("formulas") or {}).get(col[8:], ""))
        m = re.match(r'(?:note\["([^"]+)"\]|([\w ]+?))\.format\(', expr)
        if m:
            return value_text(n.prop(m.group(1) or m.group(2)))
        return ""
    return value_text(n.prop(col))


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
                src_key = "file.name" if expr.startswith("file.name") else expr.split(".")[0]
                strip_the = "/^the /i" in expr
            else:
                src_key, strip_the = key, False

            def keyf(n, src_key=src_key, strip_the=strip_the):
                raw = n.prop(src_key)
                v = n.name if src_key == "file.name" else (raw.isoformat() if isinstance(raw, datetime.date) else plain(raw))
                return (re.sub(r"^the ", "", v, flags=re.I) if strip_the else v).casefold()
            view_rows.sort(key=keyf, reverse=s.get("direction", "ASC") == "DESC")
        head = ["Name" if c == "file.name" else names.get(c, c) for c in cols]
        out.append("| " + " | ".join(head) + " |")
        out.append("| " + " | ".join(":--" for _ in cols) + " |")
        for n in view_rows:
            cells = [f"[[{n.name}]]" if c == "file.name" else base_cell(n, c, spec).replace("\n", " ") for c in cols]
            out.append("| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |")
        out.append("")
    # on the site these tables get a filter box, a drop-down per short column and click-to-sort headers
    return '<div class="covalon-filterable">\n\n' + "\n".join(out) + '\n\n</div>\n'


# ================================================================== Datacore components
def jsx_prop(src, key):
    m = re.search(rf'{key}="([^"]*)"', src)
    if m:
        return m.group(1)
    m = re.search(rf"{key}=\{{\[([^\]]*)\]\}}", src)
    if m:
        return re.findall(r'"([^"]*)"', m.group(1))
    return None


IMAGE_LINE = re.compile(r"^\s*!\[.*\]\(.*\)\s*$|^\s*!\[\[[^\]]+\.(png|jpe?g|webp|gif|svg)[^\]]*\]\]\s*$", re.I)
MISSION = re.compile(r"^### Mission ([A-Z])(?::\s*(.+?))?\s*$")


def render_missions():
    """<MissionOverview />: every expedition's missions (the tables in their ## Missions sections) in one table,
    each mission named after its expedition, e.g. "Ikouga A: Retame the Island"."""
    rows = ["| Mission | Summary |", "| :-- | :-- |"]
    for n in sorted(tagged("covalon/expedition"), key=lambda n: str(n.prop("Journey Date") or "")):
        place = n.name.removesuffix(" Expedition")
        in_missions = False
        for line in n.body.split("\n"):
            if line.startswith("## "):
                in_missions = line.strip() == "## Missions"
                continue
            if in_missions and line.strip().startswith("|"):
                cells = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
                if re.match(r"^[A-Z](?::|$)", cells[0]):
                    rows.append(f"| {place} {cells[0]} | {cells[1] if len(cells) > 1 else ''} |")
    # on the site the table gets a filter box and sortable headers
    return '<div class="covalon-filterable covalon-mission-overview">\n\n' + "\n".join(rows) + '\n\n</div>\n'


def tagline_html(note, prop):
    """A property shown as a tagline right under an entry's heading (the tagline="…" option)."""
    value = value_text(note.prop(prop)) if prop else ""
    return f'<div class="covalon-tagline">{md.renderInline(inline_markdown(value))}</div>\n\n' if value else ""


def inline_props(note, props):
    lines = []
    for k in props:
        v = note.prop(k)
        if v not in (None, "", []):
            lines.append(f"**{k}:** {value_text(v)}\n\n")
    return "".join(lines)


def render_note_aside(n, stack, inline=(), hide=()):
    """A note's text, its images floated right, a line per `inline` property, then its properties box."""
    lines = render(n, stack).split("\n")
    images = [l for l in lines if IMAGE_LINE.match(l)]
    text = "\n".join(l for l in lines if not IMAGE_LINE.match(l)).strip()
    pics = ('<div class="covalon-entry-images">\n\n' + "\n\n".join(images) + '\n\n</div>\n\n') if images else ""
    return ('<div class="covalon-entry-body">\n\n' + pics + text + "\n\n" + inline_props(n, inline)
            + props_panel(n, list(hide) + list(inline)) + '\n\n</div>')


def render_entries(src, stack):
    if "MissionOverview" in src:
        return render_missions()
    m = re.search(r'<CovalonNote\b[^>]*\bname="([^"]+)"', src)
    if m:   # one note (a district on the Gazetteer) in the aside layout, without a heading
        n = find(m.group(1))
        return ('<div class="covalon-entry-aside covalon-note">\n\n' + render_note_aside(n, stack, jsx_prop(src, "inline") or []) + '\n\n</div>') if n else ""

    tag = jsx_prop(src, "tag")
    if not tag:
        return ""
    district = jsx_prop(src, "district")
    sort_by = jsx_prop(src, "sortBy") or "name"
    level = int((jsx_prop(src, "heading") or "h2")[1])
    hide = jsx_prop(src, "hide") or []
    tagline = jsx_prop(src, "tagline")
    if tagline:
        hide = list(hide) + [tagline]
    inline = jsx_prop(src, "inline") or []   # shown as a line of text after the note's text (aside layout)
    entries = tagged(tag)
    if district:
        entries = [n for n in entries if district_of(n) == district]
    sort_prop = "date" if sort_by == "date" else sort_by
    if sort_by == "name":
        keyf = lambda n: n.name.casefold()
    elif sort_by == "title":
        keyf = lambda n: re.sub(r"^the ", "", n.name, flags=re.I).casefold()
    else:
        keyf = lambda n: (lambda v: v.isoformat() if isinstance(v, datetime.date) else plain(v))(n.prop(sort_prop))
    entries.sort(key=keyf)
    aside = bool(re.search(r"<CovalonEntries\b[^>]*\baside\b", src))
    out = []
    for n in entries:
        if aside:   # heading, the note's text, its properties; the note's images floated right beside them
            lines = shift_to(render(n, stack), level + 1).split("\n")
            images = [l for l in lines if IMAGE_LINE.match(l)]
            text = "\n".join(l for l in lines if not IMAGE_LINE.match(l)).strip()
            pics = ('<div class="covalon-entry-images">\n\n' + "\n\n".join(images) + '\n\n</div>\n\n') if images else ""
            out.append('<div class="covalon-entry covalon-entry-aside">\n\n' + f"{'#' * level} [[{n.name}]]\n\n" + tagline_html(n, tagline)
                       + '<div class="covalon-entry-body">\n\n' + pics + text + "\n\n" + inline_props(n, inline)
                       + props_panel(n, list(hide) + list(inline)) + '\n\n</div>\n\n</div>')
            continue
        part = [f"{'#' * level} [[{n.name}]]", tagline_html(n, tagline), props_panel(n, hide), shift_to(render(n, stack), level + 1)]
        out.append('<div class="covalon-entry">\n\n' + "\n\n".join(p for p in part if p) + '\n\n</div>')
    return '<div class="covalon-entries">\n\n' + "\n\n".join(out) + '\n\n</div>'


# ================================================================== embeds
EMBED = re.compile(r"(?m)^[ \t]*!\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\|[^\]]*)?\]\][ \t]*$")
CODE = re.compile(r"```(base|datacorejsx)\n(.*?)\n```", re.S)


def render_text(note, text):
    """render(), for some other text than the note's own (e.g. just a guide's introduction)."""
    body = note.body
    note.body = text
    try:
        return render(note)
    finally:
        note.body = body


def render(note, stack=()):
    if note.name in stack:
        return f"*(embed loop: {note.name})*"
    stack = stack + (note.name,)
    # blank lines around the generated HTML, so a heading right after the code block stays a heading
    text = CODE.sub(lambda m: "\n\n" + (render_base(m.group(2)) if m.group(1) == "base" else render_entries(m.group(2), stack)) + "\n\n", note.body)
    out, pos = [], 0
    for m in EMBED.finditer(text):
        out.append(text[pos:m.start()])
        target = find(m.group(1))
        if not target:
            out.append(m.group(0))
        else:
            inner = section_of(target, m.group(2)) if m.group(2) else render(target, stack)
            level = last_heading_level("".join(out))
            inner = shift_to(inner.strip(), level + 1) if level else inner.strip()
            if target.classes and not m.group(2):   # keep the embedded note's cssclasses (e.g. even-columns)
                inner = f'<div class="{" ".join(target.classes)}">\n\n{inner}\n\n</div>'
            out.append("\n" + inner + "\n")
        pos = m.end()
    out.append(text[pos:])
    return "".join(out).strip() + "\n"


# ================================================================== chapter navigation
GUIDES = ["📍 Covalon Player's Guide", "📍 Covalon GM's Guide"]
CHAPTER = re.compile(r"(?m)^# (.+)\n+!\[\[([^\]|#]+)\]\]")
NAV = {}   # chapter note name -> (guide note name, [(heading, chapter note name), ...], index)
for g in GUIDES:
    if g in notes:
        chapters = [(m.group(1).strip(), m.group(2)) for m in CHAPTER.finditer(notes[g].body)]
        for i, (_, target) in enumerate(chapters):
            NAV[target] = (g, chapters, i)


# The guides can be read two ways, picked in the settings pop-over (gear icon) and remembered in the browser:
#   paged:  an introduction page, then one page per chapter, with ← previous / next → links
#   scroll: the whole guide on one long page
# Each page knows where its headings are in the other mode, so switching keeps your place.
def intro_text(guide):
    body = notes[guide].body
    m = CHAPTER.search(body)
    return body[:m.start()] if m else body


def intro_url(guide):
    """The paged version's first page: the introduction, or chapter 1 if the guide has no introduction."""
    if not intro_text(guide).strip():
        first = next((c for c, (g, ch, i) in NAV.items() if g == guide and i == 0), None)
        if first:
            return notes[first].url
    return notes[guide].url.removesuffix("index.html") + "introduction/index.html"


def has_intro(guide):
    return bool(intro_text(guide).strip())


def nav_link(url, text, side):
    """A previous / next link: the arrow stays put while a long chapter name is cut short with "…"."""
    arrow = '<span class="chapter-nav-arrow">' + ("←" if side == "prev" else "→") + "</span>"
    name = f'<span class="chapter-nav-name">{html.escape(text)}</span>'
    return (f'<a class="internal-link" href="{href_to(url)}" title="{html.escape(text)}">'
            + (arrow + name if side == "prev" else name + arrow) + "</a>")


def chapter_nav(name):
    guide, chapters, i = NAV[name]
    prev = (nav_link(notes[chapters[i-1][1]].url, chapters[i-1][0], "prev") if i > 0
            else nav_link(intro_url(guide), "Introduction", "prev") if has_intro(guide) else "")
    nxt = nav_link(notes[chapters[i+1][1]].url, chapters[i+1][0], "next") if i + 1 < len(chapters) else ""
    return (f'<nav class="chapter-nav" data-pagefind-ignore><span class="prev">{prev}</span>'
            f'<span class="current" title="{html.escape(chapters[i][0])}">{html.escape(chapters[i][0])}</span><span class="next">{nxt}</span></nav>')


def intro_nav(guide):
    first = next(((h, c) for c, (g, ch, i) in NAV.items() if g == guide and i == 0 for h in [ch[0][0]]), None)
    nxt = nav_link(notes[first[1]].url, first[0], "next") if first else ""
    return (f'<nav class="chapter-nav" data-pagefind-ignore><span class="prev"></span>'
            f'<span class="current">Introduction</span><span class="next">{nxt}</span></nav>')


MODES = {}   # page url -> {"mode": this page's mode, "other": the same place in the other mode, "map": {id: url#id}}


def heading_ids(soup):
    return [h for h in soup.find_all(re.compile(r"^h[1-6]$")) if h.get("id")]


def plan_guide_modes():
    """Match every heading of the one-page guide with the same heading on the intro and chapter pages."""
    for g in GUIDES:
        if g not in notes:
            continue
        guide = notes[g]
        chapters = [(h, c) for c, (gg, ch, i) in sorted(NAV.items(), key=lambda kv: kv[1][2]) if gg == g for h in [ch[i][0]]]
        CUR["url"] = guide.url
        full = heading_ids(to_html(render(guide)))
        intro_heads = heading_ids(to_html(render_text(guide, intro_text(g)))) if has_intro(g) else []
        full_map, i = {}, 0
        for h in intro_heads:   # the introduction comes first on the one page too
            if i < len(full) and full[i].get_text(" ", strip=True) == h.get_text(" ", strip=True):
                full_map[full[i]["id"]] = intro_url(g) + "#" + h["id"]
                MODES.setdefault(intro_url(g), {"mode": "paged", "other": guide.url, "map": {}})["map"][h["id"]] = guide.url + "#" + full[i]["id"]
                i += 1
        if has_intro(g):
            MODES.setdefault(intro_url(g), {"mode": "paged", "other": guide.url, "map": {}})
        text = lambda h: h.get_text(" ", strip=True)
        tops = []   # where each chapter's title heading is on the one page
        for title, cname in chapters:
            k = next((k for k in range(i, len(full)) if full[k].name == "h1" and text(full[k]) == title), None)
            if k is None:
                continue
            tops.append((k, cname))
            i = k + 1
        for n, (k, cname) in enumerate(tops):
            c = notes[cname]
            section = full[k + 1:tops[n + 1][0] if n + 1 < len(tops) else len(full)]
            full_map[full[k]["id"]] = c.url
            CUR["url"] = c.url
            mine = heading_ids(to_html(render(c)))
            entry = MODES.setdefault(c.url, {"mode": "paged", "other": guide.url + "#" + full[k]["id"], "map": {}})
            j = 0
            for h in mine:   # same headings in the same order; skip any the other page doesn't have
                t = next((t for t in range(j, len(section)) if text(section[t]) == text(h)), None)
                if t is None:
                    continue
                full_map[section[t]["id"]] = c.url + "#" + h["id"]
                entry["map"][h["id"]] = guide.url + "#" + section[t]["id"]
                j = t + 1
        MODES[guide.url] = {"mode": "scroll", "other": intro_url(g), "map": full_map}


def mode_bits(url):
    """The script that takes you to your reading mode's version of this page (the mode is picked in the settings)."""
    m = MODES.get(url)
    if not m:
        return "", ""
    rel = lambda u: href_to(u.split("#")[0]) + ("#" + u.split("#")[1] if "#" in u else "")
    data = {"mode": m["mode"], "other": rel(m["other"]), "map": {k: rel(v) for k, v in m["map"].items()}}
    script = ('<script>(function(){var d=' + json.dumps(data, ensure_ascii=False).replace("</", "<\\/") + ';window.COVALON_MODE=d;'
              'var m=null;try{m=localStorage.getItem("readMode")}catch(e){}if(!m||m===d.mode)return;'
              'var h=decodeURIComponent(location.hash.slice(1));location.replace((h&&d.map[h])||d.other)})()</script>')
    return script, ""


# ================================================================== search (Pagefind)
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


def first_paragraph(soup, limit=240):
    """The page's first paragraph of running text (not in a callout, table or properties box), shortened,
    shown under a search result when there are no search words to show matches for."""
    for p in soup.find_all("p"):
        if p.find_parent(class_=re.compile(r"^(callout|covalon-props|covalon-tagline|table-wrapper|chapter-nav)")) or p.find_parent("table"):
            continue
        text = " ".join(p.get_text(" ").split())
        if len(text) < 40:
            continue
        return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0].rstrip(",;:") + "…"
    return ""


def search_markup(note, title, snippet=""):
    esc = lambda t: html.escape(str(t), quote=True)
    tags = [f'<span hidden data-pagefind-meta="title">{esc(title)}</span>',
            f'<span hidden data-pagefind-meta="snippet">{esc(snippet)}</span>' if snippet else "",
            f'<span hidden data-pagefind-sort="title">{esc(PREFIX.sub("", title).removeprefix("The ").strip())}</span>',
            f'<span hidden data-pagefind-filter="Type">{esc(page_type(note))}</span>']
    for k, v in note.props.items():
        if k.lower() in HIDDEN_PROPS or k.startswith("_") or v in (None, "", []):
            continue
        values = [plain_case(x) for x in (v if isinstance(v, list) else [v])]
        # long text makes a poor drop-down: those properties are filed under "~Name", which the
        # search's [property:text] syntax still searches but "Add filter" leaves out
        short = k.lower() not in NOT_FILTERS and all(0 < len(x) <= 40 for x in values)
        key = k if short else "~" + k
        tags += [f'<span hidden data-pagefind-filter="{esc(key)}">{esc(x)}</span>' for x in values if x]
    return "".join(tags)


# ================================================================== markdown -> Obsidian-style HTML
md = (MarkdownIt("commonmark", {"html": True, "breaks": True, "typographer": False})
      .enable(["table", "strikethrough"])
      .use(footnote_plugin)
      .use(tasklists_plugin))

CUR = {"url": "index.html"}   # the page being built (links are written relative to it)


def href_to(url):
    """A link from the page being built to `url`, relative, and without "index.html" (so /Guilds/ not /Guilds/index.html)."""
    here = os.path.dirname(CUR["url"])
    path, _, anchor = url.partition("#")
    rel = os.path.relpath(path, here or ".")
    if rel == "index.html" or rel.endswith("/index.html"):
        rel = rel[:-len("index.html")] or "./"
    return quote(rel + ("#" + anchor if anchor else ""), safe="/#-._~")


WIKILINK = re.compile(r"(!?)\[\[([^\[\]|#\\]*)(#[^\[\]|\\]*)?(?:\\?\|((?:[^\[\]]|\[[^\]]*\])*?))?\]\]")


def wikilink_html(m):
    embed, target, heading, alias = m.group(1), m.group(2), (m.group(3) or "")[1:], m.group(4)
    heading = heading.strip()
    if embed:   # a picture kept in the vault: ![[picture.webp|caption]]
        url = file_url(target)
        if not url:
            return f'<span class="internal-link is-unresolved">{html.escape(target)}</span>'
        # ![[pic.webp|caption]], ![[pic.webp|300]] or ![[pic.webp|caption|300]]: a trailing number is the width
        parts = (alias or "").split("|")
        width = parts.pop() if parts and re.fullmatch(r"\d+(x\d+)?", parts[-1].strip()) else ""
        alt = "|".join(parts).strip()
        if width:
            w = width.split("x")[0]
            return f'<img src="{href_to(url)}" alt="{html.escape(alt, quote=True)}" width="{w}">'
        return f'![{alt}](<{href_to(url)}>)'
    note = find(target) if target.strip() else None
    if target.strip() and not note:
        label = alias or target
        return f'<span class="internal-link is-unresolved">{label}</span>'
    if note:
        label = alias or (note.title + (f" > {heading}" if heading else ""))
        url = href_to(note.url) if note.url != CUR["url"] else ""
    else:   # [[#Heading]] on the same page
        label, url = alias or heading, ""
    anchor = "#" + heading_slug(heading) if heading and not heading.startswith("^") else ""
    return f'<a class="internal-link" href="{url + anchor or "#"}">{label}</a>'


def outside_code(text, fn):
    """Apply fn to the parts of the text that aren't fenced code blocks or inline code spans."""
    out, fence = [], None
    for chunk in re.split(r"(?m)(^[ \t>]*(?:```|~~~).*$)", text):
        if re.match(r"^[ \t>]*(```|~~~)", chunk or ""):
            marker = re.search(r"(```|~~~)", chunk).group(1)
            fence = None if fence == marker else (fence or marker)
            out.append(chunk)
        elif fence:
            out.append(chunk)
        else:
            parts = re.split(r"(`+[^`\n]*?`+)", chunk)
            out.append("".join(p if i % 2 else fn(p) for i, p in enumerate(parts)))
    return "".join(out)


def inline_markdown(text):
    """Obsidian's extra syntax turned into things markdown understands: wikilinks, ==highlights==, %%comments%%."""
    def fix(t):
        t = re.sub(r"%%.*?%%", "", t, flags=re.S)
        t = WIKILINK.sub(wikilink_html, t)
        t = re.sub(r"(?<!=)==(?=\S)(.+?)(?<=\S)==(?!=)", r"<mark>\1</mark>", t)
        return t
    return outside_code(text, fix)


def inline_html(text):
    return md.renderInline(inline_markdown(text))


# ---- icons (Lucide, the icon set Obsidian and Callout Manager use)
ICON_CACHE = pathlib.Path(os.environ.get("COVALON_CACHE", pathlib.Path.home() / ".cache" / "covalon-site"))
_icons = None


def lucide(name):
    """The SVG for a Lucide icon, e.g. 'pencil' or 'lucide-pencil'. Downloaded once and cached."""
    global _icons
    if _icons is None:
        _icons = {}
        tgz = next(iter(sorted(ICON_CACHE.glob("lucide-static-*.tgz"))), None)
        if tgz is None:
            try:
                meta = json.load(urllib.request.urlopen("https://registry.npmjs.org/lucide-static/latest", timeout=30))
                ICON_CACHE.mkdir(parents=True, exist_ok=True)
                tgz = ICON_CACHE / f"lucide-static-{meta['version']}.tgz"
                tgz.write_bytes(urllib.request.urlopen(meta["dist"]["tarball"], timeout=120).read())
            except Exception as e:   # offline: callouts just go without icons
                print(f"warning: couldn't download the Lucide icons ({e}); callouts will have no icons", file=sys.stderr)
                return ""
        with tarfile.open(tgz) as t:
            for member in t.getmembers():
                m = re.match(r"package/icons/(.+)\.svg$", member.name)
                if m:
                    _icons[m.group(1)] = t.extractfile(member).read().decode()
    key = name.removeprefix("lucide-")
    svg = _icons.get(key, "")
    if not svg:
        return ""
    svg = re.sub(r"<!--.*?-->", "", svg, flags=re.S).strip()
    return re.sub(r'class="[^"]*"', f'class="svg-icon lucide-{key}"', svg, count=1)


# ---- callouts: Obsidian's built-in types, plus Callout Manager's changes
BUILTIN = {   # type: (icon, colour name)
    "note": ("pencil", "blue"), "abstract": ("clipboard-list", "cyan"), "summary": ("clipboard-list", "cyan"),
    "tldr": ("clipboard-list", "cyan"), "info": ("info", "blue"), "todo": ("check-circle-2", "blue"),
    "tip": ("flame", "cyan"), "hint": ("flame", "cyan"), "important": ("flame", "cyan"),
    "success": ("check", "green"), "check": ("check", "green"), "done": ("check", "green"),
    "question": ("help-circle", "orange"), "help": ("help-circle", "orange"), "faq": ("help-circle", "orange"),
    "warning": ("alert-triangle", "orange"), "caution": ("alert-triangle", "orange"), "attention": ("alert-triangle", "orange"),
    "failure": ("x", "red"), "fail": ("x", "red"), "missing": ("x", "red"),
    "danger": ("zap", "red"), "error": ("zap", "red"), "bug": ("bug", "red"),
    "example": ("list", "purple"), "quote": ("quote", "gray"), "cite": ("quote", "gray"),
}
CM_FILE = SRC / ".obsidian" / "plugins" / "callout-manager" / "data.json"
CM = json.loads(CM_FILE.read_text()).get("callouts", {}) if CM_FILE.exists() else {}


_SNIPPET_ICONS = None


def snippet_icons():
    """Callout icons drawn as SVG in the vault's snippets: .callout[data-callout="dino"] { --callout-icon: '<svg…>'; }"""
    global _SNIPPET_ICONS
    if _SNIPPET_ICONS is None:
        _SNIPPET_ICONS = {}
        for f in sorted((SRC / ".obsidian" / "snippets").glob("*.css")):
            css = f.read_text(encoding="utf-8")
            for m in re.finditer(r'\.callout\[data-callout="([^"]+)"\]\s*\{([^}]*)\}', css):
                icon = re.search(r"--callout-icon:\s*'(<svg.*?</svg>)'", m.group(2), re.S)
                if icon:
                    _SNIPPET_ICONS[m.group(1)] = icon.group(1)
    return _SNIPPET_ICONS


def callout_icon_html(kind):
    svg = snippet_icons().get(kind)
    if svg:   # same classes as a Lucide icon, so it's sized and coloured the same way
        return svg.replace("<svg ", f'<svg class="svg-icon callout-icon-{kind}" ', 1)
    return lucide(callout_icon(kind))


def callout_icon(kind):
    icon = None
    for s in (CM.get("settings") or {}).get(kind, []):
        if not s.get("condition") and (s.get("changes") or {}).get("icon"):
            icon = s["changes"]["icon"]
    return icon or BUILTIN.get(kind, ("pencil", "blue"))[0]


def callouts_css():
    """Callout colours from Callout Manager, written the way the plugin writes them in Obsidian."""
    out = ["/* Generated from Callout Manager's settings by build.py. Change colours in Obsidian (Settings → Callout Manager). */"]
    for kind, entries in sorted((CM.get("settings") or {}).items()):
        for s in entries:
            color = (s.get("changes") or {}).get("color")
            if not color:
                continue
            scheme = (s.get("condition") or {}).get("colorScheme") if isinstance(s.get("condition"), dict) else None
            if s.get("condition") and not scheme:
                continue   # conditions on a specific Obsidian theme don't apply to the site
            pre = f".theme-{scheme} " if scheme else ""
            out.append(f'{pre}.callout[data-callout="{kind}"] {{ --callout-color: rgb({color}); }}')
    return "\n".join(out) + "\n"


CALLOUT_HEAD = re.compile(r"^\s*\[!([^\]|\s]+)(?:\|([^\]]*))?\]([+-]?)[ \t]*")


def make_callout(soup, bq):
    first = bq.find(recursive=False)
    if not first or first.name != "p" or not first.contents or not isinstance(first.contents[0], NavigableString):
        return
    m = CALLOUT_HEAD.match(str(first.contents[0]))
    if not m:
        return
    kind, meta, fold = m.group(1).lower(), (m.group(2) or "").strip(), m.group(3)
    first.contents[0].replace_with(str(first.contents[0])[m.end():])
    # the title is everything up to the first line break; the rest of that paragraph is content
    title_nodes, rest = [], []
    for node in list(first.contents):
        if rest or (isinstance(node, Tag) and node.name == "br"):
            rest.append(node)
        else:
            title_nodes.append(node)
    if rest and isinstance(rest[0], Tag) and rest[0].name == "br":
        rest = rest[1:]
    box = soup.new_tag("div", attrs={"class": "callout", "data-callout": kind,
                                     "data-callout-metadata": meta, "data-callout-fold": fold})
    if fold:
        box["class"] = ["callout", "is-collapsible"] + (["is-collapsed"] if fold == "-" else [])
    title = soup.new_tag("div", attrs={"class": "callout-title"})
    icon = soup.new_tag("div", attrs={"class": "callout-icon"})
    icon.append(BeautifulSoup(callout_icon_html(kind), "html.parser"))
    inner = soup.new_tag("div", attrs={"class": "callout-title-inner"})
    if "".join(str(n) for n in title_nodes).strip():
        for n in title_nodes:
            inner.append(n.extract())
    else:
        inner.string = kind[:1].upper() + kind[1:]
    title.extend([icon, inner])
    if fold:
        chevron = soup.new_tag("div", attrs={"class": "callout-fold"})
        chevron.append(BeautifulSoup(lucide("chevron-down"), "html.parser"))
        title.append(chevron)
    content = soup.new_tag("div", attrs={"class": "callout-content"})
    if rest and "".join(str(n) for n in rest).strip():
        p = soup.new_tag("p")
        for n in rest:
            p.append(n.extract())
        content.append(p)
    first.decompose()
    for child in list(bq.children):
        content.append(child.extract())
    box.extend([title, content])
    bq.replace_with(box)


WRAP = {"p": "el-p", "ul": "el-ul", "ol": "el-ol", "table": "el-table", "pre": "el-pre", "hr": "el-hr",
        "blockquote": "el-blockquote", "figure": "el-p", "section": "el-section", "div": "el-div",
        **{f"h{i}": f"el-h{i}" for i in range(1, 7)}}
CONTAINERS = {"covalon-entries", "covalon-entry", "covalon-filterable", "covalon-entry-body", "covalon-note"}


def wrap_blocks(soup, parent):
    """Obsidian puts every top-level block of a note in its own <div class="el-…"> in reading view;
    the vault's snippets rely on that (e.g. a heading followed by a table)."""
    for child in list(parent.children):
        if isinstance(child, NavigableString):
            continue
        cls = set(child.get("class") or [])
        if child.name == "div" and (cls & CONTAINERS or child.has_attr("data-pagefind-body") or cls & set(ALL_CSSCLASSES)):
            wrap_blocks(soup, child)
            continue
        wrapper_cls = WRAP.get(child.name)
        if not wrapper_cls or (cls & {"covalon-props", "chapter-nav"}):
            continue
        wrapper = soup.new_tag("div", attrs={"class": wrapper_cls})
        child.wrap(wrapper)


ALL_CSSCLASSES = sorted({c for n in notes.values() for c in n.classes})


def to_html(markdown):
    soup = BeautifulSoup(md.render(inline_markdown(markdown)), "html.parser")
    for bq in soup.find_all("blockquote"):
        make_callout(soup, bq)
    # images with alt text become captioned figures (like the Image Captions plugin)
    for img in soup.find_all("img"):
        img["loading"] = "lazy"
        p = img.parent
        if img.get("alt") and p and p.name == "p" and len([c for c in p.contents if str(c).strip()]) == 1:
            fig = soup.new_tag("figure", attrs={"class": "image-captions-figure"})
            cap = soup.new_tag("figcaption", attrs={"class": "image-captions-caption"})
            cap.string = img["alt"]
            fig.extend([img.extract(), cap])
            p.replace_with(fig)
    for a in soup.find_all("a", href=True):
        if re.match(r"https?://|mailto:", a["href"]):
            a["class"] = (a.get("class") or []) + ["external-link"]
            a["target"], a["rel"] = "_blank", "noopener"
    # headings: anchors (unique per page) and data-heading, like Obsidian
    seen = {}
    for h in soup.find_all(re.compile(r"^h[1-6]$")):
        text = h.get_text(" ", strip=True)
        base = heading_slug(text)
        seen[base] = seen.get(base, 0) + 1
        h["id"] = base if seen[base] == 1 else f"{base}-{seen[base] - 1}"
        h["data-heading"] = text
    for table in soup.find_all("table"):
        table.wrap(soup.new_tag("div", attrs={"class": "table-wrapper"})) if table.parent.name != "div" or "table-wrapper" not in (table.parent.get("class") or []) else None
    wrap_blocks(soup, soup)
    return soup


# ================================================================== page frame
def toc_html(soup, title=None):
    heads = [h for h in soup.find_all(re.compile(r"^h[1-4]$")) if not h.find_parent(class_="callout")]
    if not heads:
        return ""
    items, stack = [], []
    if title:   # the page's own title first: back to the top
        items.append(f'<li class="toc-title"><a href="#page-title">{html.escape(title)}</a></li>')
    base = min(int(h.name[1]) for h in heads)
    for h in heads:
        depth = int(h.name[1]) - base
        items.append(f'<li class="toc-depth-{depth}"><a href="#{h["id"]}">{html.escape(h.get_text(" ", strip=True))}</a></li>')
    return '<nav class="site-toc"><div class="site-panel-title">On this page</div><ul>' + "".join(items) + "</ul></nav>"


def natural(s):
    return [int(t) if t.isdigit() else t.casefold() for t in re.split(r"(\d+)", s)]


def tree_html(current):
    """The file tree in the sidebar (like Obsidian's file explorer)."""
    root = {}
    for n in notes.values():
        node = root
        for f in n.folders:
            node = node.setdefault(("folder", f), {})
        node[("file", n.title)] = n

    def order(item):
        (kind, name), _ = item
        first = FIRST.index(name) if name in FIRST else len(FIRST)
        pinned = 0 if kind == "file" and isinstance(item[1], Note) and item[1].name.startswith("📍") else 1
        return (first, pinned, kind != "folder", natural(name))

    def walk(node, depth):
        out = []
        for (kind, name), child in sorted(node.items(), key=order):
            if kind == "folder":
                inside = any(n is current for n in iter_notes(child))
                out.append(f'<details class="tree-folder"{" open" if inside else ""}><summary class="tree-item tree-folder-title">'
                           f'{lucide("chevron-right")}<span>{html.escape(name)}</span></summary>'
                           f'<div class="tree-children">{walk(child, depth + 1)}</div></details>')
            else:
                cls = "tree-item tree-file" + (" is-active" if child is current else "")
                pin = '<span class="tree-pin" aria-hidden="true">📍</span>' if child.name.startswith("📍") else ""   # pinned overviews keep their pin, as in Obsidian
                out.append(f'<a class="{cls}{" is-pinned" if pin else ""}" href="{href_to(child.url)}">{pin}{html.escape(name)}</a>')
        return "".join(out)
    return f'<nav class="site-tree">{walk(root, 0)}</nav>'


def iter_notes(node):
    for v in node.values():
        if isinstance(v, Note):
            yield v
        else:
            yield from iter_notes(v)


SNIPPETS = []   # the vault's enabled CSS snippets, in Obsidian's order


LOGO = "Covalon-Logo-Bold-Wood-Cropped-Small.webp"   # also the browser-tab icon


def favicon(root):
    url = file_url(LOGO)
    return f'<link rel="icon" type="image/webp" href="{root}{url}">' if url else ""


def setting(name, label, options):
    buttons = "".join(f'<button type="button" class="site-setting-option" data-value="{v}">{lucide(icon)}{text}</button>'
                      for v, icon, text in options)
    return (f'<div class="site-setting" data-setting="{name}"><div class="site-setting-label">{label}</div>'
            f'<div class="site-setting-options" role="group" aria-label="{label}">{buttons}</div></div>')


# the settings pop-over behind the gear icon (site.js makes it work; choices are kept in the browser)
SETTINGS = ('<div class="site-settings" hidden role="dialog" aria-label="Settings">'
            + setting("theme", "Appearance", [("light", "sun", "Light"), ("dark", "moon", "Dark"), ("auto", "monitor", "Auto")])
            + setting("readMode", "Guides", [("paged", "book-open", "Paged"), ("scroll", "scroll-text", "Scroll")])
            + '<p class="site-setting-note">Paged shows the Player\'s and GM\'s Guides a chapter at a time; Scroll shows each guide on one long page.</p>'
            + setting("spoilers", "Spoilers", [("hide", "eye-off", "Hidden"), ("show", "eye", "Shown")])
            + '<p class="site-setting-note">GM sections on the adventure type pages are hidden until you click them, unless spoilers are shown.</p>'
            + "</div>")


def page(title, body_html, toc, current=None, extra_head="", search_page=False, url=None):
    mode_script, mode_switch = mode_bits(url or CUR["url"])
    root = href_to("index.html").removesuffix("index.html")
    css = ["assets/base.css"] + [f"assets/snippets/{s}.css" for s in SNIPPETS] + ["assets/callouts.css", "assets/site.css"]
    links = "".join(f'<link rel="stylesheet" href="{root}{c}">' for c in css)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}{"" if title == SITE_TITLE else " · " + SITE_TITLE}</title>
{mode_script}{links}{favicon(root)}{extra_head}
</head>
<body class="theme-light">
<script>(function(){{var t=null;try{{t=localStorage.getItem("theme")}}catch(e){{}}if(!t)t=matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light";document.body.className=document.documentElement.className="theme-"+t;try{{if(localStorage.getItem("spoilers")==="show")document.documentElement.classList.add("show-spoilers")}}catch(e){{}}}})()</script>
<div class="site">
  <aside class="site-sidebar site-left workspace-split mod-left-split">
    <div class="site-header">
      <a class="site-title" href="{root}">{SITE_TITLE}</a>
      <button class="site-settings-toggle" type="button" title="Settings" aria-label="Settings" aria-haspopup="true" aria-expanded="false">{lucide("settings")}</button>
      {SETTINGS}
    </div>
    <form class="site-search" action="{root}search/" role="search">
      {lucide("search")}<input type="search" name="q" placeholder="Search…" aria-label="Search the guides"><kbd>⌘K</kbd>
    </form>
    {tree_html(current)}
  </aside>
  <main class="site-main">
    <div class="markdown-preview-view markdown-rendered{" is-search-page" if search_page else ""}">
      <div class="markdown-preview-sizer">
        <div class="inline-title" id="page-title">{html.escape(title)}</div>
        {body_html}
      </div>
    </div>
  </main>
  <aside class="site-sidebar site-right workspace-split mod-right-split">{toc}</aside>
</div>
<button class="site-menu-button" type="button" aria-label="Menu">{lucide("menu")}</button>
<script src="{root}assets/site.js"></script>
<script src="{root}assets/search.js"></script>
</body>
</html>
"""


# ================================================================== entry pages look like their overview
ENTRY_STYLE = {}   # tag -> how the overview page shows its entries (CovalonEntries options)
NOTE_STYLE = {}    # note name -> the same, for notes shown one by one (CovalonNote, e.g. the districts)


def collect_entry_styles():
    for n in notes.values():
        for m in CODE.finditer(n.body):
            if m.group(1) != "datacorejsx":
                continue
            src = m.group(2)
            one = re.search(r'<CovalonNote\b[^>]*\bname="([^"]+)"', src)
            if one:
                target = find(one.group(1))
                if target:
                    NOTE_STYLE.setdefault(target.name, {"aside": True, "tagline": None, "inline": jsx_prop(src, "inline") or []})
                continue
            tag = jsx_prop(src, "tag")
            if tag and "<CovalonEntries" in src:
                ENTRY_STYLE.setdefault(tag, {"aside": bool(re.search(r"<CovalonEntries\b[^>]*\baside\b", src)),
                                             "tagline": jsx_prop(src, "tagline"), "inline": jsx_prop(src, "inline") or []})


def entry_style(note):
    if note.name.startswith("📍"):
        return None
    return NOTE_STYLE.get(note.name) or next((st for tag, st in ENTRY_STYLE.items() if tag in note.tags), None)


# Adventure type pages (outside the GM's Guide) hide their "For GMs" section behind a spoiler, so players
# don't read it by accident. Clicking it shows it; the settings pop-over can show all spoilers.
SPOILER_FOLDERS = {"Adventure Types"}
SPOILER_HEADINGS = {"for gms"}


def spoiler_sections(soup):
    for h in soup.find_all(re.compile(r"^h[1-6]$")):
        if h.get_text(" ", strip=True).casefold() not in SPOILER_HEADINGS or h.find_parent(class_="callout"):
            continue
        block = h.parent if h.parent and (h.parent.get("class") or [""])[0].startswith("el-h") else h
        level = int(h.name[1])
        section = []
        for sib in block.find_next_siblings():
            inner = sib.find(re.compile(r"^h[1-6]$"), recursive=False) if sib.name == "div" else sib
            if inner is not None and re.match(r"^h[1-6]$", inner.name or "") and int(inner.name[1]) <= level:
                break
            section.append(sib)
        if not section:
            continue
        wrap = soup.new_tag("div", attrs={"class": "covalon-spoiler"})
        content = soup.new_tag("div", attrs={"class": "covalon-spoiler-content"})
        button = BeautifulSoup('<button type="button" class="covalon-spoiler-reveal">' + lucide("eye")
                               + '<span>GM section: click to show</span></button>', "html.parser")
        section[0].insert_before(wrap)
        for el in section:
            content.append(el.extract())
        wrap.append(button)
        wrap.append(content)


def build_note(note):
    CUR["url"] = note.url
    title = NAV[note.name][1][NAV[note.name][2]][0] if note.name in NAV else note.title
    style = entry_style(note)
    if style and style["aside"]:   # tagline, text with images floated right, inline properties, properties box at the bottom
        body = (tagline_html(note, style["tagline"]) + '<div class="covalon-entry covalon-entry-aside">\n\n'
                + render_note_aside(note, (), style["inline"], [style["tagline"]] if style["tagline"] else []) + '\n\n</div>\n')
    elif style:                    # tagline, properties box, then the text
        hide = [style["tagline"]] if style["tagline"] else []
        body = ('<div class="covalon-entry">\n\n' + tagline_html(note, style["tagline"]) + props_panel(note, hide)
                + "\n\n" + render(note) + '\n\n</div>\n')
    else:
        body = render(note)
    if note.classes:
        body = f'<div class="{" ".join(note.classes)}">\n\n{body.strip()}\n\n</div>\n'
    soup = to_html(body)
    if note.path.relative_to(SRC).parts[0] in SPOILER_FOLDERS:
        spoiler_sections(soup)
    parts = [str(soup)] if style else [props_panel(note), str(soup)]
    if note.name in NAV:
        nav = chapter_nav(note.name)
        parts = [nav] + parts + [nav]
    content = "\n".join(p for p in parts if p)
    if not note.name.startswith("📍"):   # overview pages repeat their entries' text, so they're left out of search
        content = f'<div data-pagefind-body>{search_markup(note, title, first_paragraph(soup))}{content}</div>'
    write(note.url, page(title, content, toc_html(soup, title), current=note))
    if note.name in GUIDES and has_intro(note.name):   # the paged version's first page: the guide's introduction
        CUR["url"] = intro_url(note.name)
        isoup = to_html(render_text(note, intro_text(note.name)))
        nav = intro_nav(note.name)
        write(CUR["url"], page(title, "\n".join([nav, str(isoup), nav]), toc_html(isoup, title), current=note))


HOME = """Welcome to the Covalon guides: everything you need to play in, or run games for, Covalon, a Pathfinder 2nd Edition living world campaign.

## The guides

- [[📍 Covalon Player's Guide|Covalon Player's Guide]]: the full player's guide on one page.
- [[📍 Covalon GM's Guide|Covalon GM's Guide]]: the full guide for Dungeon Guides on one page.
- [[📍 Adventure Types|Adventure Types]]: every kind of adventure Covalon runs.
- <a class="internal-link" href="search/">Advanced search</a>: search every page, filtered by page type and properties (deity domains, soul seeds, districts and more).

## The world

- [[📍 Covalon Gazetteer|Covalon Gazetteer]]
- [[📍 Guilds|Guilds]]
- [[📍 Pre-Cataclysm Civilizations|Pre-Cataclysm Civilizations]]
- [[📍 Expeditions|Expeditions]] and the [[📍 Mission Overview|Mission Overview]]
- [[📍 Deities, Faith, and Ideologies|Deities, Faith, and Ideologies]]
- [[📍 Campaign Events|Campaign Events]]

<p class="site-credits">Some icons by Delapouite and Lorc from <a href="https://game-icons.net">game-icons.net</a>, licensed <a href="https://creativecommons.org/licenses/by/3.0/">CC BY 3.0</a>.</p>
"""

SEARCH = """Search every page of the guides. Pick a page type, then use **Add filter** to narrow the results by properties such as a deity's domains, an expedition's soul seed or a location's district (“is” or “is not”). The same search opens over any page from the search box in the sidebar, or with Ctrl K / ⌘ K.

<div id="search"></div>
"""


def write(url, text):
    dest = OUT / url
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    # styles: the stand-in for Obsidian's theme, the vault's enabled snippets, callout colours, the site frame
    appearance = SRC / ".obsidian" / "appearance.json"
    enabled = json.loads(appearance.read_text()).get("enabledCssSnippets", []) if appearance.exists() else []
    (OUT / "assets" / "snippets").mkdir(parents=True)
    for name in enabled:
        f = SRC / ".obsidian" / "snippets" / f"{name}.css"
        if f.exists():
            shutil.copy(f, OUT / "assets" / "snippets" / f.name)
            SNIPPETS.append(name)
    for f in (HERE / "assets").iterdir():
        if f.is_file():
            shutil.copy(f, OUT / "assets" / f.name)
    (OUT / "assets" / "callouts.css").write_text(callouts_css(), encoding="utf-8")

    collect_entry_styles()
    plan_guide_modes()
    file_url(LOGO)
    for n in notes.values():
        build_note(n)
    for src, url in USED_FILES.items():   # the vault's pictures the pages use
        dest = OUT / url
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dest)
    CUR["url"] = "index.html"
    write("index.html", page(SITE_TITLE, str(to_html(HOME)), ""))
    CUR["url"] = "search/index.html"
    search_head = ""
    write("search/index.html", page("Advanced Search", str(to_html(SEARCH)), "", extra_head=search_head, search_page=True))
    print(f"wrote {len(notes) + 2} pages to {OUT}")


if __name__ == "__main__":
    main()
