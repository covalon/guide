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
import hashlib
import html
import io
import json
import os
import pathlib
import re
import urllib.parse
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
FIRST = ["Home", "Player's Guide", "GM's Guide"]   # shown first in the sidebar, in this order


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


# Names sort without a leading "The" or "Kingdom of" (The Kingdom of Varceta sorts as Varceta), as in the
# vault's bases and Datacore lists (their formulas use /^(the )?(kingdom of )?/i).
SORT_PREFIX = re.compile(r"^(?:the )?(?:kingdom of )?", re.I)


def sort_name(text):
    return SORT_PREFIX.sub("", text)


def slug(text):
    """File and anchor names: letters and digits kept (any language), apostrophes dropped (the-teachers-union,
    not the-teacher-s-union), everything else becomes '-'."""
    return re.sub(r"[^\w]+", "-", re.sub(r"['’‘`]", "", text)).strip("-") or "page"


# Short addresses for some folders and pages; every other folder and page is its name in lower case,
# with plain letters for accented ones (/guilds/the-archivists/, /civilizations/pudersno/)
# A page can pick its own address with a `_url` property (e.g. `_url: briarmurk` on The Briarmurk).
FOLDER_URLS = {"Player's Guide": "players", "GM's Guide": "gms", "Tables": "table", "City of Covalon": "city"}


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
    if n.name in notes:   # two notes with the same name (e.g. each guide's "Chapter 0 - Introduction"): like
        # Obsidian, tell them apart by their folder path ("📄 GM's Guide/Chapter 0 - Introduction")
        other = notes.pop(n.name)
        other.name = str(other.path.relative_to(SRC).with_suffix(""))
        notes[other.name] = other
        n.name = str(rel.with_suffix(""))
    elif any(str(m.path.relative_to(SRC).with_suffix("")).endswith("/" + n.name) for m in notes.values()):
        n.name = str(rel.with_suffix(""))   # a third note with an already-shared name
    notes[n.name] = n

# The home page (/) is the note "📍 Home" in the vault's top folder, so it can be edited in Obsidian.
HOME_NOTE = "📍 Home"
if HOME_NOTE in notes:
    notes[HOME_NOTE].url = "index.html"

# A folder's pinned overview (📍) is the folder's own page: /Guilds/ rather than /Guilds/Guilds/.
# With several pinned notes in a folder, the one named after the folder gets it (/Expeditions/), and the
# others keep their own address (/Expeditions/Mission-Overview/).
_pinned = {}
for n in notes.values():
    if n.name.startswith("📍") and n.folders:
        _pinned.setdefault(tuple(n.folders), []).append(n)
FOLDER_HOME = {}   # folder (as a tuple of names) -> its pinned overview note, for the breadcrumbs
for folders, group in _pinned.items():
    main = group[0] if len(group) == 1 else next((n for n in group if n.title == folders[-1]), None)
    if main:
        main.url = "/".join(url_part(p) for p in folders) + "/index.html"
        FOLDER_HOME[folders] = main
# A folder without a pinned overview whose note has the folder's own name (City of Covalon/Armory District/
# Armory District) makes that note the folder's page, too: /city/armory-district/.
for n in notes.values():
    folders = tuple(n.folders)
    if folders and folders not in FOLDER_HOME and n.title == folders[-1]:
        n.url = "/".join(url_part(p) for p in folders) + "/index.html"
        FOLDER_HOME[folders] = n

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
    target = target.strip().replace("''", "'").removesuffix(".md")
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
        value = md.renderInline(inline_markdown(list_markup(v)))
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
def list_markup(v):
    """A list property, each item (with its comma) kept together when the line wraps: links are shown as
    inline blocks, which would otherwise let a comma drop onto a line of its own."""
    if not isinstance(v, list):
        return value_text(v)
    items = [value_text(x) for x in v if x not in (None, "")]
    return " ".join(f'<span class="covalon-list-item">{x}{"," if i < len(items) - 1 else ""}</span>' for i, x in enumerate(items))


def base_cell(n, col, spec):
    if col.startswith("formula."):   # the formulas the vault uses: a date property shown with .format(...)
        expr = str((spec.get("formulas") or {}).get(col[8:], ""))
        m = re.match(r'(?:note\["([^"]+)"\]|([\w ]+?))\.format\(', expr)
        if m:
            return value_text(n.prop(m.group(1) or m.group(2)))
        return ""
    return list_markup(n.prop(col))


def render_base(src, this=None):
    """A base's table views. `this` is the note the base is in (for filters like District.linksTo(this.file))."""
    spec = yaml.safe_load(src) or {}
    filters = (spec.get("filters") or {}).get("and", [])
    rows = list(notes.values())
    for f in filters:
        f = str(f)
        m = re.match(r'file\.hasTag\("([^"]+)"\)', f)
        if m:
            rows = [n for n in rows if m.group(1) in n.tags]
            continue
        m = re.match(r'(\w[\w ]*?)\.linksTo\(this(?:\.file)?\)$', f.strip())
        if m:   # the property links to the note the base is in
            key = m.group(1)
            targets = (this.name, this.title) if this else ()
            rows = [n for n in rows if (district_of(n) if key.lower() == "district" else
                    (lambda r: (re.search(r"\[\[([^\]|#]+)", r) or re.match(r"(.*)", r)).group(1).strip())(value_text(n.prop(key, "")))) in targets]
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
                strip_the = "/^the /i" in expr or "/^(the )?(kingdom of )?/i" in expr
            else:
                src_key, strip_the = key, False

            def keyf(n, src_key=src_key, strip_the=strip_the):
                raw = n.prop(src_key)
                v = n.name if src_key == "file.name" else (raw.isoformat() if isinstance(raw, datetime.date) else plain(raw))
                return (sort_name(v) if strip_the else v).casefold()
            view_rows.sort(key=keyf, reverse=s.get("direction", "ASC") == "DESC")
        head = ["Name" if c == "file.name" else names.get(c, c) for c in cols]
        out.append("| " + " | ".join(head) + " |")
        out.append("| " + " | ".join(":--" for _ in cols) + " |")
        for n in view_rows:
            # (spoilers become their HTML here, before the cells' pipes are escaped for the table)
            cells = [f"[[{n.name}]]" if c == "file.name" else spoiler_html(base_cell(n, c, spec).replace("\n", " ")) for c in cols]
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


def props_with_images(props, images):
    """The properties box and the note's pictures side by side (2/3 and 1/3), the pictures fitted to the
    box's height: the imagesBesideProps option (the guilds' heraldry)."""
    if not images:
        return props
    return ('<div class="covalon-props-row">\n\n' + props + '\n\n<div class="covalon-props-images">\n\n'
            + "\n\n".join(images) + '\n\n</div>\n\n</div>')


def render_note_aside(n, stack, inline=(), hide=(), props_first=False, beside=False, own_page=False):
    """A note's text, its images floated right, a line per `inline` property, and its properties box
    (after the text, or before it with props_first)."""
    lines = render(n, stack, bases=own_page).split("\n")
    images = [l for l in lines if IMAGE_LINE.match(l)]
    text = "\n".join(l for l in lines if not IMAGE_LINE.match(l)).strip()
    pics = ('<div class="covalon-entry-images">\n\n' + "\n\n".join(images) + '\n\n</div>\n\n') if images else ""
    props = props_panel(n, list(hide) + list(inline))
    if beside:
        props, pics = props_with_images(props, images), ""
    return ('<div class="covalon-entry-body">\n\n' + pics + (props + "\n\n" if props_first else "") + text + "\n\n"
            + inline_props(n, inline) + ("" if props_first else props) + '\n\n</div>')


def entries_for(src):
    """The notes a <CovalonEntries … /> block lists, in its order (tag, district, sortBy)."""
    tag = jsx_prop(src, "tag")
    district = jsx_prop(src, "district")
    sort_by = jsx_prop(src, "sortBy") or "name"
    entries = tagged(tag)
    if district:
        entries = [n for n in entries if district_of(n) == district]
    sort_prop = "date" if sort_by == "date" else sort_by
    if sort_by == "name":
        keyf = lambda n: n.name.casefold()
    elif sort_by == "title":
        keyf = lambda n: sort_name(n.name).casefold()
    else:
        keyf = lambda n: (lambda v: v.isoformat() if isinstance(v, datetime.date) else plain(v))(n.prop(sort_prop))
    entries.sort(key=keyf)
    return entries


def render_list(src):
    """<CovalonList tag="…" where="…" is="…" after="…" />: the tagged notes as a bulleted list of links."""
    tag, where, is_, after = (jsx_prop(src, k) for k in ("tag", "where", "is", "after"))
    rows = [n for n in tagged(tag or "") if not where or plain(n.prop(where)).strip().casefold() == (is_ or "").strip().casefold()]
    rows.sort(key=lambda n: sort_name(n.name).casefold())
    lines = []
    for n in rows:
        extra = n.prop(after) if after else None
        lines.append(f"- [[{n.name}]]" + (f" ({list_markup(extra)})" if extra not in (None, "", []) else ""))
    return "\n".join(lines)


def render_entries(src, stack):
    if "MissionOverview" in src:
        return render_missions()
    if "<CovalonList" in src:
        return render_list(src)
    m = re.search(r'<CovalonNote\b[^>]*\bname="([^"]+)"', src)
    if m:   # one note (a district on the Gazetteer) in the aside layout, without a heading
        n = find(m.group(1))
        return ('<div class="covalon-entry-aside covalon-note">\n\n' + render_note_aside(n, stack, jsx_prop(src, "inline") or [], props_first=bool(re.search(r"<CovalonNote\b[^>]*\bpropsFirst\b", src))) + '\n\n</div>') if n else ""

    tag = jsx_prop(src, "tag")
    if not tag:
        return ""
    level = int((jsx_prop(src, "heading") or "h2")[1])
    hide = jsx_prop(src, "hide") or []
    tagline = jsx_prop(src, "tagline")
    if tagline:
        hide = list(hide) + [tagline]
    inline = jsx_prop(src, "inline") or []   # shown as a line of text after the note's text (aside layout)
    entries = entries_for(src)
    aside = bool(re.search(r"<CovalonEntries\b[^>]*\baside\b", src))
    props_first = bool(re.search(r"<CovalonEntries\b[^>]*\bpropsFirst\b", src))
    beside = bool(re.search(r"<CovalonEntries\b[^>]*\bimagesBesideProps\b", src))
    out = []
    for n in entries:
        if aside:   # heading, the note's text, its properties; the note's images floated right beside them
            lines = shift_to(render(n, stack, bases=False), level + 1).split("\n")
            images = [l for l in lines if IMAGE_LINE.match(l)]
            text = "\n".join(l for l in lines if not IMAGE_LINE.match(l)).strip()
            pics = ('<div class="covalon-entry-images">\n\n' + "\n\n".join(images) + '\n\n</div>\n\n') if images else ""
            props = props_panel(n, list(hide) + list(inline))
            if beside:
                props, pics = props_with_images(props, images), ""
            # the images come first, then the heading, so they float from the top of the entry
            out.append('<div class="covalon-entry covalon-entry-aside">\n\n<div class="covalon-entry-body">\n\n' + pics
                       + f"{'#' * level} [[{n.name}]]\n\n" + tagline_html(n, tagline)
                       + (props + "\n\n" if props_first else "") + text + "\n\n"
                       + inline_props(n, inline) + ("" if props_first else props) + '\n\n</div>\n\n</div>')
            continue
        part = [f"{'#' * level} [[{n.name}]]", tagline_html(n, tagline), props_panel(n, hide), shift_to(render(n, stack), level + 1)]
        out.append('<div class="covalon-entry">\n\n' + "\n\n".join(p for p in part if p) + '\n\n</div>')
    return '<div class="covalon-entries">\n\n' + "\n\n".join(out) + '\n\n</div>'


# ================================================================== image alignment (Image Converter plugin)
# The Image Converter plugin keeps each picture's alignment (left / center / right, wrap text or not, and a
# width) in .obsidian/image-converter-image-alignments.json, under the note and a hash of
# "<note path>:<picture path>". The site gives the same pictures the same alignment.
def _alignments():
    f = SRC / ".obsidian" / "image-converter-image-alignments.json"
    try:
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    except ValueError:
        return {}


def _alignment_settings():
    f = SRC / ".obsidian" / "plugins" / "image-converter" / "data.json"
    try:
        d = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    except ValueError:
        d = {}
    return d.get("isImageAlignmentEnabled", False), d.get("imageAlignmentDefaultAlignment", "none")


ALIGNMENTS = _alignments()
ALIGN_ENABLED, ALIGN_DEFAULT = _alignment_settings()


_M32 = 0xFFFFFFFF
def rotl(x, r): return ((x << r) | (x >> (32 - r))) & _M32
def mul(a, b): return (a * b) & _M32
def fmix(h):
    h ^= h >> 16; h = mul(h, 2246822507); h ^= h >> 13; h = mul(h, 3266489909); h ^= h >> 16; return h
def plugin_hash(text):
    b = [ord(c) & 255 for c in text.encode("utf-16-le").decode("latin-1")[::2]]   # low byte of each UTF-16 unit
    s = len(b); a, o = 2277735313, 1291169091
    r = t = n = f = 0
    def k(x): x = mul(x, a); x = rotl(x, 15); return mul(x, o)
    word = lambda i: b[i] | b[i+1] << 8 | b[i+2] << 16 | b[i+3] << 24
    for blk in range(s >> 4):
        p = 16 * blk
        r ^= k(word(p)); r = rotl(r, 19); r = (mul(r, 5) + 3864292196) & _M32
        t ^= k(word(p + 4)); t = rotl(t, 17); t = (mul(t, 5) + 3864292196) & _M32
        n ^= k(word(p + 8)); n = rotl(n, 15); n = (mul(n, 5) + 3864292196) & _M32
        f ^= k(word(p + 12)); f = rotl(f, 13); f = (mul(f, 5) + 3864292196) & _M32
    c = 16 * (s >> 4); d = s % 16
    lanes = [0, 0, 0, 0]
    for i in range(d):
        lanes[i // 4] ^= b[c + i] << (8 * (i % 4))
    if d > 12: f ^= k(lanes[3])
    if d > 8: n ^= k(lanes[2])
    if d > 4: t ^= k(lanes[1])
    if d > 0: r ^= k(lanes[0])
    r ^= s; t ^= s; n ^= s; f ^= s
    r = (r + t) & _M32; r = (r + n) & _M32; r = (r + f) & _M32
    t = (t + r) & _M32; t = (t + n) & _M32; t = (t + f) & _M32
    n = (n + r) & _M32; n = (n + t) & _M32; n = (n + f) & _M32
    f = (f + r) & _M32; f = (f + t) & _M32; f = (f + n) & _M32
    r, t, n, f = fmix(r), fmix(t), fmix(n), fmix(f)
    return f"{f:08x}{n:08x}{t:08x}{r:08x}"


PICTURE_EMBED = re.compile(r"!\[\[([^\]|#]+\.(?:png|jpe?g|webp|gif|svg|avif|bmp))((?:\|[^\]]*)?)\]\]", re.I)


def align_pictures(note, text):
    """Mark each picture embedded in this note with its alignment: ![[pic.webp|caption|@align=left,wrap,300px]]."""
    if not ALIGN_ENABLED:
        return text
    note_path = str(note.path.relative_to(SRC))
    saved = ALIGNMENTS.get(note_path, {})

    def mark(m):
        pic = files.get(m.group(1).strip().split("/")[-1].casefold())
        if not pic:
            return m.group(0)
        a = saved.get(plugin_hash(f"{note_path}:{pic.relative_to(SRC)}"))
        if a is None:
            if ALIGN_DEFAULT in (None, "", "none"):
                return m.group(0)
            a = {"position": ALIGN_DEFAULT, "wrap": False}
        if a.get("position") in (None, "", "none"):
            return m.group(0)
        spec = ",".join([a["position"], "wrap" if a.get("wrap") else "nowrap", str(a.get("width") or ""), str(a.get("height") or "")])
        return f"![[{m.group(1)}{m.group(2) or '|'}{'|' if m.group(2) else ''}@align={spec}]]"
    return PICTURE_EMBED.sub(mark, text)


# ================================================================== embeds
EMBED = re.compile(r"(?m)^[ \t]*!\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\|[^\]]*)?\]\][ \t]*$")
CODE = re.compile(r"```(base|datacorejsx)\n(.*?)\n```", re.S)


# A note's own bases (with the heading just above them), left out where the note is shown inside a list
# on another page, e.g. a district's "## Locations" table on the Gazetteer, which lists them already.
OWN_BASE = re.compile(r"(?m)(^#{1,6} [^\n]*\n+)?^```base\n.*?\n```[ \t]*\n?", re.S)


def render(note, stack=(), bases=True):
    if note.name in stack:
        return f"*(embed loop: {note.name})*"
    stack = stack + (note.name,)
    body = align_pictures(note, note.body if bases else OWN_BASE.sub("", note.body))
    # blank lines around the generated HTML, so a heading right after the code block stays a heading
    code = lambda t, where: CODE.sub(lambda m: "\n\n" + (render_base(m.group(2), where) if m.group(1) == "base" else render_entries(m.group(2), stack)) + "\n\n", t)
    text = code(body, note)
    out, pos = [], 0
    for m in EMBED.finditer(text):
        out.append(text[pos:m.start()])
        target = find(m.group(1))
        if not target:
            out.append(m.group(0))
        else:
            # an embedded section's bases and Datacore views are drawn too (e.g. ![[Expeditions#For Players]])
            inner = code(section_of(target, m.group(2)), target) if m.group(2) else render(target, stack)
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
CHAPTER_FILE = re.compile(r"^Chapter (\d+) - (.+)$")


def guide_chapters(guide):
    """<CovalonGuide />: the chapter notes in the guide's own folder ("Chapter 3 - Covalon Gameplay"), in
    number order, each under its heading ("# Chapter 3: Covalon Gameplay"; chapter 0 is "# Introduction")."""
    found = []
    for n in notes.values():
        m = CHAPTER_FILE.match(n.title)
        if m and n.path.parent == guide.path.parent:
            found.append((int(m.group(1)), "Introduction" if m.group(1) == "0" else f"Chapter {int(m.group(1))}: {m.group(2)}", n.name))
    return "\n".join(f"# {heading}\n![[{name}]]" for _, heading, name in sorted(found))


for g in GUIDES:   # a guide written as <CovalonGuide /> lists its chapters itself (Obsidian does the same with Datacore)
    if g in notes and "<CovalonGuide" in notes[g].body:
        notes[g].body = CODE.sub(lambda m: guide_chapters(notes[g]) if m.group(1) == "datacorejsx" and "<CovalonGuide" in m.group(2) else m.group(0),
                                 notes[g].body)
NAV = {}   # chapter note name -> (guide note name, [(heading, chapter note name), ...], index)
for g in GUIDES:
    if g in notes:
        chapters = [(m.group(1).strip(), m.group(2)) for m in CHAPTER.finditer(notes[g].body)]
        for i, (_, target) in enumerate(chapters):
            NAV[target] = (g, chapters, i)


# Each guide is two things on the site: its pinned note is the whole guide on one long page (/players/), and
# its chapters (the notes it embeds under "# …" headings, starting with its Introduction) are pages of their
# own to page through with ← previous / next → links.


def nav_link(url, text, side):
    """A previous / next link: the arrow stays put while a long chapter name is cut short with "…"."""
    arrow = '<span class="chapter-nav-arrow">' + ("←" if side == "prev" else "→") + "</span>"
    name = f'<span class="chapter-nav-name">{html.escape(text)}</span>'
    return (f'<a class="internal-link" href="{href_to(url)}" title="{html.escape(text)}">'
            + (arrow + name if side == "prev" else name + arrow) + "</a>")


def chapter_nav(name):
    guide, chapters, i = NAV[name]
    prev = nav_link(notes[chapters[i-1][1]].url, chapters[i-1][0], "prev") if i > 0 else ""
    nxt = nav_link(notes[chapters[i+1][1]].url, chapters[i+1][0], "next") if i + 1 < len(chapters) else ""
    return (f'<nav class="chapter-nav" data-pagefind-ignore><span class="prev">{prev}</span>'
            f'<span class="current" title="{html.escape(chapters[i][0])}">{html.escape(chapters[i][0])}</span><span class="next">{nxt}</span></nav>')


# ================================================================== search (Pagefind)
TYPES = {"Deities": "Deity", "Guilds": "Guild", "City of Covalon": "Location", "Civilizations": "Civilization",
         "Expeditions": "Expedition", "Campaign Events": "Campaign Event", "Adventure Types": "Adventure Type"}
# Properties left out of the search filters: long text, dates, and lists too long to be useful as filters
NOT_FILTERS = {"order", "description", "tagline", "expedition summary", "roleplay channel",
               "edicts", "anathema", "membership requirements", "goals", "values", "date", "journey date",
               "finale first cleared", "expedition log", "population", "created by", "cleric spells", "members", "leader",
               "pantheon members", "guild headquarters of", "primary exports", "finale", "fate"}


def page_type(note):
    top = note.path.relative_to(SRC).parts[0]
    if top.startswith("📄"):
        return "Table" if note.name.startswith("Table ") else PREFIX.sub("", top)
    return TYPES.get(top, top)


def first_paragraph(soup, limit=240, spoiler=lambda text: "▒▒▒▒"):
    """The page's first paragraph of running text (not in a callout, table or properties box), shortened,
    shown under a search result when there are no search words to show matches for. ||Spoilers|| in it
    are shown by `spoiler` (blanked out by default)."""
    for p in soup.find_all("p"):
        if p.find_parent(class_=re.compile(r"^(callout|covalon-props|covalon-tagline|table-wrapper|chapter-nav)")) or p.find_parent("table"):
            continue
        if p.select(".covalon-inline-spoiler"):
            p = BeautifulSoup(str(p), "html.parser").p
            for sp in p.select(".covalon-inline-spoiler"):
                sp.replace_with(spoiler(" ".join(sp.get_text(" ").split())))
        text = " ".join(p.get_text(" ").split())
        if len(text) < 40:
            continue
        return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0].rstrip(",;:") + "…"
    return ""


# Pages that other pages point to in a property are found by that property too, without showing it:
# Alatar is an expedition's Civilization, so [civilization:alatar] finds the Alatar page as well as the
# Alatar Expedition. (note name -> {property: {value as the other pages show it}})
LINKED_AS = {}


def collect_linked_as():
    for n in notes.values():
        for k, v in n.props.items():
            if k.lower() in HIDDEN_PROPS or k.startswith("_"):
                continue
            for item in (v if isinstance(v, list) else [v]):
                for m in re.finditer(r"\[\[([^\]|#]+)", str(item or "")):
                    target = find(m.group(1))
                    if target and target is not n:
                        LINKED_AS.setdefault(target.name, {}).setdefault(k, set()).add(plain_case(item))


def search_markup(note, title, snippet=""):
    esc = lambda t: html.escape(str(t), quote=True)
    tags = [f'<span hidden data-pagefind-meta="title">{esc(title)}</span>',
            f'<span hidden data-pagefind-meta="snippet">{esc(snippet)}</span>' if snippet else "",
            f'<span hidden data-pagefind-sort="title">{esc(sort_name(PREFIX.sub("", title)).strip())}</span>',
            f'<span hidden data-pagefind-filter="Type">{esc(page_type(note))}</span>']
    for k, v in note.props.items():
        if k.lower() in HIDDEN_PROPS or k.startswith("_") or v in (None, "", []):
            continue
        values = [plain_case(x) for x in (v if isinstance(v, list) else [v])]
        values = [SPOILER.sub(r"\1", x) for x in values]   # ||spoilers|| are filters like any other value
        # long text makes a poor drop-down: those properties are filed under "~Name", which the
        # search's [property:text] syntax still searches but "Add filter" leaves out
        short = k.lower() not in NOT_FILTERS and all(0 < len(x) <= 40 for x in values)
        key = k if short else "~" + k
        tags += [f'<span hidden data-pagefind-filter="{esc(key)}">{esc(x)}</span>' for x in values if x]
    own = {k.lower() for k in note.props}
    for k, values in LINKED_AS.get(note.name, {}).items():
        if k.lower() in own:
            continue
        key = k if k.lower() not in NOT_FILTERS else "~" + k
        tags += [f'<span hidden data-pagefind-filter="{esc(key)}">{esc(x)}</span>' for x in sorted(values) if x]
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


def align_attrs(align):
    """"left,wrap,300px," (from align_pictures) -> the Image Converter plugin's classes, and a style for its size."""
    pos, wrap, w_css, h_css = (align.split(",") + ["", "", "", ""])[:4]
    cls = f'image-converter-aligned image-position-{pos} {"image-wrap" if wrap == "wrap" else "image-no-wrap"}'
    style = "".join(f"{k}:{v};" for k, v in (("width", w_css), ("height", h_css)) if v)
    return cls, style


def wikilink_html(m):
    embed, target, heading, alias = m.group(1), m.group(2), (m.group(3) or "")[1:], m.group(4)
    heading = heading.strip()
    if embed:   # a picture kept in the vault: ![[picture.webp|caption]]
        url = file_url(target)
        if not url:
            return f'<span class="internal-link is-unresolved">{html.escape(target)}</span>'
        # ![[pic.webp|caption]], ![[pic.webp|300]] or ![[pic.webp|caption|300]]: a trailing number is the width
        parts = (alias or "").split("|")
        align = parts.pop()[len("@align="):] if parts and parts[-1].startswith("@align=") else ""
        width = parts.pop() if parts and re.fullmatch(r"\d+(x\d+)?", parts[-1].strip()) else ""
        alt = "|".join(parts).strip()
        # the width and alignment ride along in the picture's title; to_html turns them into attributes.
        # (Written as a Markdown picture, not an <img> tag: an <img> at the start of a line would make
        # Markdown treat the lines after it as raw HTML, up to the next blank line.)
        extra = " ".join(x for x in [f"w={width.split('x')[0]}" if width else "", f"align={align}" if align else ""] if x)
        return f'![{alt}](<{href_to(url)}>' + (f' "@img {extra}"' if extra else "") + ")"
    note = find(target) if target.strip() else None
    if target.strip() and not note:
        label = alias or target
        return f'<span class="internal-link is-unresolved">{label}</span>'
    if note:
        # without an alias the link reads as written, like in Obsidian (📍 pins and all), minus any folder path
        label = alias or (target.strip().split("/")[-1] + (f" > {heading}" if heading else ""))
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


# ||spoilers||, as in Discord (and Obsidian's Inline spoilers plugin): hidden until clicked
SPOILER = re.compile(r"(?<!\|)\|\|(?=\S)(.+?)(?<=\S)\|\|(?!\|)")


def spoiler_html(text):
    return SPOILER.sub(r'<span class="covalon-inline-spoiler" tabindex="0" role="button" aria-label="Spoiler: click to show" '
                       r'title="Spoiler: click to show"><span class="covalon-inline-spoiler-text">\1</span></span>', text)


def inline_markdown(text):
    """Obsidian's extra syntax turned into things markdown understands: wikilinks, ==highlights==, %%comments%%,
    ||spoilers||."""
    def fix(t):
        t = re.sub(r"%%.*?%%", "", t, flags=re.S)
        t = WIKILINK.sub(wikilink_html, t)
        t = re.sub(r"(?<!=)==(?=\S)(.+?)(?<=\S)==(?!=)", r"<mark>\1</mark>", t)
        return spoiler_html(t)
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
        sized = False
        if img.get("title", "").startswith("@img "):
            for part in img["title"][5:].split():
                key, _, val = part.partition("=")
                if key == "w":
                    img["width"], sized = val, True
                elif key == "align":
                    cls, style = align_attrs(val)
                    img["class"] = (img.get("class") or []) + cls.split()
                    if style:
                        img["style"] = style
            del img["title"]
        p = img.parent
        if img.get("alt") and p and p.name == "p" and len([c for c in p.contents if str(c).strip()]) == 1:
            fig = soup.new_tag("figure", attrs={"class": "image-captions-figure"})
            aligned = [c for c in img.get("class", []) if c.startswith("image-")]
            if aligned:   # the caption goes with the picture: the figure is what's aligned / wrapped
                fig["class"] = ["image-captions-figure"] + aligned
                img["class"] = [c for c in img["class"] if c not in aligned]
                if not img["class"]:
                    del img["class"]
            cap = soup.new_tag("figcaption", attrs={"class": "image-captions-caption"})
            cap.string = img["alt"]
            fig.extend([img.extract(), cap])
            p.replace_with(fig)
    # table columns are at least as wide as their widest cell's text on one line, or 10 characters,
    # whichever is less (and never narrower than their header, which doesn't wrap), so short columns
    # don't get squeezed into a word per line
    for table in soup.find_all("table"):
        heads = table.select("thead tr:first-child > th")
        widths = [0] * len(heads)
        for tr in table.find_all("tr"):
            for i, cell in enumerate(tr.find_all(["th", "td"], recursive=False)[:len(heads)]):
                widths[i] = max(widths[i], len(" ".join(cell.get_text(" ").split())))
        for th, w in zip(heads, widths):
            if w:
                th["style"] = (th.get("style", "").rstrip("; ") + "; " if th.get("style") else "") + f"min-width: min(10ch, {w + 1}ch)"
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
    return '<nav class="site-toc"><div class="site-panel-title">On this page</div><ul class="site-toc-list">' + "".join(items) + "</ul></nav>"


def natural(s):
    return [int(t) if t.isdigit() else t.casefold() for t in re.split(r"(\d+)", s)]


# Entries whose overview lists them in an order of its own (sortBy a property: Adventure Types by Order,
# Expeditions by Journey Date, Campaign Events by date) keep that order in the sidebar too, instead of A–Z.
OVERVIEW_RANK = {}   # note name -> its place on its overview (filled in by collect_entry_order)


def tree_root():
    root = {}
    for n in notes.values():
        node = root
        for f in n.folders:
            node = node.setdefault(("folder", f), {})
        node[("file", n.title)] = n
    return root


def tree_order(item):
    """The sidebar's order (also used by the entry pages' previous / next links)."""
    (kind, name), child = item
    first = FIRST.index(name) if name in FIRST else len(FIRST)
    pinned = 0 if isinstance(child, Note) and (child.name.startswith("📍") or FOLDER_HOME.get(tuple(child.folders)) is child) else 1   # a folder's own page first
    last = 1 if kind == "folder" and name == "Tables" else 0   # a guide's Tables folder goes below its chapters
    chapter = NAV[child.name][2] if isinstance(child, Note) and child.name in NAV else 999   # guide chapters in reading order
    ranked = OVERVIEW_RANK.get(child.name, 10**6) if isinstance(child, Note) else 10**6   # e.g. expeditions by journey date
    return (first, last, pinned, kind != "folder", chapter, ranked, natural(sort_name(name)))   # then A–Z ignoring "The" and "Kingdom of"


def sidebar_positions():
    """Each note's place in the sidebar, top to bottom with every folder open."""
    pos = {}
    def walk(node):
        for (kind, name), child in sorted(node.items(), key=tree_order):
            if kind == "folder":
                walk(child)
            else:
                pos[child.name] = len(pos)
    walk(tree_root())
    return pos


def tree_html(current):
    """The file tree in the sidebar (like Obsidian's file explorer)."""
    root = tree_root()
    order = tree_order

    def walk(node, depth, path=()):
        out = []
        for (kind, name), child in sorted(node.items(), key=order):
            if kind == "folder":
                inside = any(n is current for n in iter_notes(child))
                home = FOLDER_HOME.get(path + (name,))
                # a folder with a pinned overview: its name opens the overview (where the folder is shown
                # open); the arrow just folds / unfolds it
                label = (f'<a class="tree-folder-link" href="{href_to(home.url)}">{html.escape(name)}</a>' if home
                         else f'<span>{html.escape(name)}</span>')
                out.append(f'<details class="tree-folder"{" open" if inside else ""}><summary class="tree-item tree-folder-title">'
                           f'{lucide("chevron-right")}{label}</summary>'
                           f'<div class="tree-children">{walk(child, depth + 1, path + (name,))}</div></details>')
            else:
                cls = "tree-item tree-file" + (" is-active" if child is current else "")
                pin = '<span class="tree-pin" aria-hidden="true">📍</span>' if child.name.startswith("📍") else ""   # pinned overviews keep their pin, as in Obsidian
                icon = re.match(r"^([^\w\s'\"(\[]+)\s+(.*)$", name)   # a note named with an icon (🔎 How to Search) keeps it, set like the pins
                label = (f'<span class="tree-pin" aria-hidden="true">{html.escape(icon.group(1))}</span>{html.escape(icon.group(2))}'
                         if icon and not pin else html.escape(name))
                out.append(f'<a class="{cls}{" is-pinned" if pin or icon else ""}" href="{href_to(child.url)}">{pin}{label}</a>')
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
    buttons = "".join(f'<button type="button" class="site-setting-option" data-value="{v}">{icon if icon.startswith("<") else lucide(icon)}{text}</button>'
                      for v, icon, text in options)
    return (f'<div class="site-setting" data-setting="{name}"><div class="site-setting-label">{label}</div>'
            f'<div class="site-setting-options" role="group" aria-label="{label}">{buttons}</div></div>')


# Fonts: sans serif (the default, the vault's usual look) or serif (the original Homebrewery guide's
# fonts, the original-guide-fonts snippet). That snippet isn't bundled into style.css: the page adds it
# only when "Serif" is picked, so nobody else downloads the fonts.
SERIF_SNIPPET = "original-guide-fonts"
FONTS_SETTING = setting("fonts", "Font", [
    ("sans", '<span class="site-font-sample is-sans" aria-hidden="true">Aa</span>', "Sans serif"),
    ("serif", '<span class="site-font-sample is-serif" aria-hidden="true">Aa</span>', "Serif")])


# the settings pop-over behind the gear icon (site.js makes it work; choices are kept in the browser)
SETTINGS = ('<div class="site-settings" hidden role="dialog" aria-label="Settings">'
            + setting("theme", "Appearance", [("light", "sun", "Light"), ("dark", "moon", "Dark"), ("auto", "monitor", "Auto")])
            + setting("textSize", "Text size", [("small", "a-arrow-down", "Small"), ("default", "type", "Default"),
                                                ("large", "a-arrow-up", "Large"), ("larger", "a-arrow-up", "Larger")])
            + setting("width", "Page width", [("readable", "align-center", "Readable"), ("wide", "move-horizontal", "Wide")])
            + FONTS_SETTING
            + setting("spoilers", "Spoilers", [("hide", "eye-off", "Hidden"), ("show", "eye", "Shown")])
            + '<p class="site-setting-note">GM sections on the adventure type pages are hidden until you click them, unless spoilers are shown.</p>'
            + "</div>")


ASSET_VERSIONS = {}   # asset file -> its link with a version stamp (filled in by main)

# Pictures are copied into the site at most PICTURE_MAX_WIDTH pixels wide and re-compressed, so pages
# don't download multi-megabyte originals. The vault's own files are left as they are. Animated pictures
# (e.g. the crashed orb) are copied unchanged. Results are cached next to the icons, so it's only slow once.
PICTURE_MAX_WIDTH = 1800
PICTURE_QUALITY = 82


def copy_picture(src, dest):
    if src.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
        shutil.copy(src, dest)
        return
    key = hashlib.sha256(src.read_bytes() + f"|{PICTURE_MAX_WIDTH}|{PICTURE_QUALITY}".encode()).hexdigest()[:20]
    cached = ICON_CACHE / "pictures" / (key + src.suffix.lower())
    if not cached.exists():
        try:
            from PIL import Image
            with Image.open(src) as im:
                if getattr(im, "is_animated", False):
                    raise ValueError("animated")
                im.load()
                if im.width > PICTURE_MAX_WIDTH:
                    im = im.resize((PICTURE_MAX_WIDTH, round(im.height * PICTURE_MAX_WIDTH / im.width)), Image.LANCZOS)
                fmt = {".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG", ".webp": "WEBP"}[src.suffix.lower()]
                if fmt == "JPEG" and im.mode not in ("RGB", "L"):
                    im = im.convert("RGB")
                cached.parent.mkdir(parents=True, exist_ok=True)
                tmp = cached.with_name(cached.name + ".tmp")
                opts = {"optimize": True} if fmt == "PNG" else {"quality": PICTURE_QUALITY, "method": 4} if fmt == "WEBP" else {"quality": PICTURE_QUALITY, "optimize": True, "progressive": True}
                im.save(tmp, fmt, **opts)
            # keep whichever is smaller (a small original can already be better compressed)
            if tmp.stat().st_size < src.stat().st_size:
                tmp.replace(cached)
            else:
                tmp.unlink()
                shutil.copy(src, cached)
        except Exception:
            shutil.copy(src, dest)
            return
    shutil.copy(cached, dest)


def breadcrumbs(note, title):
    """Home › Guilds › The Archivists: each folder links to its pinned overview, at this page's own entry
    (or chapter) where it has one, so it's one click from an entry to its place in the big overview."""
    if note.name == HOME_NOTE:
        return ""
    link = lambda url, text: f'<a class="internal-link" href="{href_to(url)}">{html.escape(text)}</a>'
    crumbs = [link("index.html", "Home")]
    for depth in range(1, len(note.folders) + 1):
        folders = tuple(note.folders[:depth])
        home = FOLDER_HOME.get(folders)
        if home is note:
            break
        if home is None:
            crumbs.append(f'<span>{html.escape(folders[-1])}</span>')
            continue
        at = ""
        if depth == len(note.folders) and not is_overview(note):   # jump to this page's entry / chapter there
            anchor = NAV[note.name][1][NAV[note.name][2]][0] if note.name in NAV and NAV[note.name][0] == home.name else note.title
            at = "#" + heading_slug(anchor)
        crumbs.append(link(home.url + at, home.title))
    crumbs.append(f'<span aria-current="page">{html.escape(title)}</span>')
    return ('<nav class="site-breadcrumbs" aria-label="Breadcrumbs" data-pagefind-ignore>'
            + '<span class="site-breadcrumbs-sep" aria-hidden="true">›</span>'.join(crumbs) + "</nav>")


def page(title, body_html, toc, current=None, extra_head="", search_page=False, url=None, crumbs="", title_side=""):
    root = href_to("index.html").removesuffix("index.html")
    links = f'<link rel="stylesheet" href="{root}assets/{ASSET_VERSIONS["style.css"]}">'
    scripts = "".join(f'<script src="{root}assets/{ASSET_VERSIONS[js]}" defer></script>' for js in ("site.js", "search.js"))
    return f"""<!doctype html>
<html lang="en" data-root="{root}" data-serif-fonts="{root}assets/{ASSET_VERSIONS.get(SERIF_SNIPPET + '.css', '')}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(SITE_TITLE if title == SITE_TITLE else SITE_TITLE + " | " + title)}</title>
{links}{scripts}{favicon(root)}{extra_head}
</head>
<body class="theme-light">
<script>(function(){{var t=null;try{{t=localStorage.getItem("theme")}}catch(e){{}}if(!t)t=matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light";document.body.className=document.documentElement.className="theme-"+t;try{{if(localStorage.getItem("spoilers")==="show")document.documentElement.classList.add("show-spoilers");if(localStorage.getItem("width")==="wide")document.documentElement.classList.add("wide-mode");var ts=localStorage.getItem("textSize");if(ts)document.documentElement.classList.add("text-"+ts);if(localStorage.getItem("fonts")==="serif"){{var fl=document.createElement("link");fl.rel="stylesheet";fl.id="serif-fonts";fl.href=document.documentElement.dataset.serifFonts;document.head.appendChild(fl)}}}}catch(e){{}}}})()</script>
<div class="site">
  <aside class="site-sidebar site-left workspace-split mod-left-split">
    <div class="site-sidebar-top">
    <div class="site-header">
      <a class="site-title" href="{root}">{SITE_TITLE}</a>
      <button class="site-settings-toggle" type="button" title="Settings" aria-label="Settings" aria-haspopup="true" aria-expanded="false">{lucide("settings")}</button>
      {SETTINGS}
    </div>
    <form class="site-search" action="{root}search/" role="search">
      {lucide("search")}<input type="search" name="q" placeholder="Search…" aria-label="Search the guides"><kbd>⌘K</kbd>
    </form>
    </div>
    {tree_html(current)}
  </aside>
  <main class="site-main">
    <div class="markdown-preview-view markdown-rendered{" is-search-page" if search_page else ""}">
      <div class="markdown-preview-sizer">
        {crumbs}{f'<div class="page-title-row">' if title_side else ""}<div class="inline-title" id="page-title">{html.escape(title)}</div>{title_side + "</div>" if title_side else ""}
        {body_html}
      </div>
    </div>
  </main>
  <aside class="site-sidebar site-right workspace-split mod-right-split">{toc}</aside>
</div>
<button class="site-menu-button" type="button" aria-label="Menu">{lucide("menu")}</button>
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
                    NOTE_STYLE.setdefault(target.name, {"aside": True, "tagline": None, "inline": jsx_prop(src, "inline") or [],
                                                         "props_first": bool(re.search(r"<CovalonNote\b[^>]*\bpropsFirst\b", src))})
                continue
            tag = jsx_prop(src, "tag")
            if tag and "<CovalonEntries" in src:
                ENTRY_STYLE.setdefault(tag, {"aside": bool(re.search(r"<CovalonEntries\b[^>]*\baside\b", src)),
                                             "props_first": bool(re.search(r"<CovalonEntries\b[^>]*\bpropsFirst\b", src)),
                                             "beside": bool(re.search(r"<CovalonEntries\b[^>]*\bimagesBesideProps\b", src)),
                                             "tagline": jsx_prop(src, "tagline"), "inline": jsx_prop(src, "inline") or []})


ENTRY_ORDER = {}   # entry note name -> (overview note, [entry notes in the overview's order], index)


def collect_entry_order():
    """Entry pages (a deity, a guild, a location …) get ← previous / next → links through the list on their
    overview page (its CovalonEntries and CovalonNote blocks), in the order the sidebar lists them."""
    for o in notes.values():
        if is_overview(o):
            ranked = [n for m in CODE.finditer(o.body) if m.group(1) == "datacorejsx" and "<CovalonEntries" in m.group(2)
                      and jsx_prop(m.group(2), "tag") and (jsx_prop(m.group(2), "sortBy") or "name") not in ("name", "title")
                      for n in entries_for(m.group(2))]
            for i, n in enumerate(ranked):
                OVERVIEW_RANK.setdefault(n.name, i)
    pos = sidebar_positions()
    for o in notes.values():
        if not is_overview(o) or o.name in GUIDES or o.name == HOME_NOTE or o.path.relative_to(SRC).parts[0].startswith("📄"):
            continue
        order = []
        for m in CODE.finditer(o.body):
            if m.group(1) != "datacorejsx":
                continue
            src = m.group(2)
            one = re.search(r'<CovalonNote\b[^>]*\bname="([^"]+)"', src)
            if one:
                n = find(one.group(1))
                order += [n] if n else []
            elif "<CovalonEntries" in src and jsx_prop(src, "tag"):
                order += entries_for(src)
        seen = []
        for n in order:
            if n not in seen:
                seen.append(n)
        seen.sort(key=lambda n: pos.get(n.name, len(pos)))   # in the sidebar's order, so the links match it
        for i, n in enumerate(seen):
            ENTRY_ORDER.setdefault(n.name, (o, seen, i))


def entry_nav(name):
    o, order, i = ENTRY_ORDER[name]
    prev = nav_link(order[i-1].url, order[i-1].title, "prev") if i > 0 else ""
    nxt = nav_link(order[i+1].url, order[i+1].title, "next") if i + 1 < len(order) else ""
    cur = order[i].title
    return (f'<nav class="chapter-nav entry-nav" data-pagefind-ignore><span class="prev">{prev}</span>'
            f'<span class="current" title="{html.escape(cur)}">{html.escape(cur)}</span><span class="next">{nxt}</span></nav>')


def is_overview(note):
    """A pinned (📍) note that lists other notes (Guilds, the Gazetteer …). A pinned note that is itself an
    entry on an overview (a district, pinned to the top of its folder) is still an entry page."""
    return note.name.startswith("📍") and note.name not in NOTE_STYLE and not any(t in ENTRY_STYLE for t in note.tags)


def entry_style(note):
    if is_overview(note):
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


BUILD_DATE = datetime.datetime.now(datetime.timezone.utc).date()


# ================================================================== link previews (Discord and others)
# Each page carries a Discord "component embed" (a small card made of Discord's own components, read by
# Discord's crawler from the page's HTML; https://discord.com/developers/docs → Link Previews) plus the usual
# Open Graph tags, which Discord falls back to and other apps (iMessage, Slack, WhatsApp …) use.
SITE_URL = "https://covalon.github.io/guide/"   # where the site is published: previews need full addresses
SITE_NAME = "Covalon Guides"
PREVIEW_COLOR = "#d6b46a"   # the dark-mode accent (Discord is mostly used in dark mode)
# A note can pick its card's thumbnail with a hidden property: `_preview: "[[CovalonCity.webp]]"`.
# the properties shown in bold on an entry's card, by the entry's tag
PREVIEW_PROPS = {
    "covalon/deity": ["Domains", "Divine Font", "Favored Weapon"],
    "covalon/guild": ["Leader", "Headquarters"],
    "covalon/civilization": ["Covalon Status"],
    "covalon/location": ["District"],
    "covalon/district": [],
    "covalon/expedition": ["Civilization", "Soul Seed", "Journey Date"],
    "covalon/event": ["Type", "Date"],
    "covalon/adventure-type": ["Duration"],
}


def absolute(url):
    """A site-relative address (players/chapter-1/index.html) as a full, encoded one."""
    url = url.removesuffix("index.html")
    return SITE_URL + urllib.parse.quote(url, safe="/#:?=&-._~%")


def md_escape(text):
    """Plain text made safe inside Discord markdown: its formatting characters, and a # - > or number
    that would start a heading, list or quote at the beginning of a line."""
    text = re.sub(r"([\\*_~`|\[\]])", r"\\\1", text)
    return re.sub(r"(?m)^(\s*)([#>-]|\d+\.)", r"\1\\\2", text)


def shorten(text, limit):
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0].rstrip(",;:.") + "…"


def first_picture(note):
    """The site address of the first picture the note shows (e.g. a guild's heraldry), or None."""
    for m in PICTURE_EMBED.finditer(note.body):
        url = file_url(m.group(1).strip())
        if url:
            return url
    return None


def preview_trail(note):
    """Where the page sits, for the card's small print: Player's Guide › Chapter 3 …"""
    parts, folders = [], tuple(note.folders)
    for depth in range(1, len(folders) + 1):
        home = FOLDER_HOME.get(folders[:depth])
        if home is note:
            continue
        parts.append(home.title if home else folders[depth - 1])
    if note.name in NAV and not parts:
        parts.append(notes[NAV[note.name][0]].title)
    return " › ".join(parts)


def link_button(label, url):
    return {"type": 2, "style": 5, "label": shorten(label, 78), "url": url}


def preview_head(note, title, soup):
    page_url = absolute(note.url)
    lines, buttons = [], [link_button("Open in the guide", page_url)]
    tagline = plain_case(note.prop("Tagline") or note.prop("Description") or "")
    hidden = []   # ||spoilers|| in the first paragraph: Discord spoilers on the card
    def keep_spoiler(text):
        hidden.append(text)
        return f"\u2063{len(hidden) - 1}\u2063"
    blurb = first_paragraph(soup, 300, keep_spoiler)
    if note.name == HOME_NOTE:
        blurb = first_paragraph(soup, 300) or "The Covalon guides."
        buttons = [link_button(notes[g].title, absolute(notes[g].url)) for g in GUIDES if g in notes]
        how = find("🔎 How to Search")
        if how:
            buttons.append(link_button("How to Search", absolute(how.url)))
    table = re.match(r"Table (\d+-\d+) - (.*)$", note.title)
    if table and note.folders and note.folders[-1] == "Tables":   # Table 3-1: … — from which chapter, and its columns
        title = f"Table {table.group(1)}: {table.group(2)}"
        chapter = next((c for c, (g, ch, i) in NAV.items() if re.search(r"!\[\[" + re.escape(note.name) + r"[\]|#]", notes[c].body)), None)
        if chapter:
            ch = NAV[chapter][1][NAV[chapter][2]][0]
            lines.append("From " + md_escape(ch))
            buttons.append(link_button("Open " + ch.split(":")[0], absolute(notes[chapter].url)))
        cols = [" ".join(th.get_text(" ").split()) for th in soup.find_all("th")]
        if cols:
            lines.append("**Columns** " + md_escape(" · ".join(cols[:8])))
        blurb = ""
    if tagline:
        lines.append("*" + md_escape(shorten(tagline, 150)) + "*")
    if blurb and blurb != tagline:
        lines.append(re.sub("\u2063(\\d+)\u2063", lambda m: "||" + md_escape(hidden[int(m.group(1))]) + "||", md_escape(blurb)))
    blurb = re.sub("\u2063\\d+\u2063", "▒▒▒▒", blurb)   # the plain description (other apps) keeps them hidden
    # key properties (entries)
    for tag, keys in PREVIEW_PROPS.items():
        if tag in note.tags:
            facts = []
            for k in keys:
                v = note.prop(k)
                if v not in (None, "", []):
                    facts.append(f"**{md_escape(k)}** {md_escape(shorten(plain_case(v), 80))}")
            if facts:   # ||spoilers|| in a property stay Discord spoilers
                lines.append(re.sub(r"\\\|\\\|(.+?)\\\|\\\|", r"||\1||", " · ".join(facts)))
            break
    # chapters: their main sections; a whole guide: its chapters
    if note.name in NAV or note.name in GUIDES:
        level = "h1" if note.name in GUIDES else "h2"
        heads = [(" ".join(h.get_text(" ").split()), h.get("id")) for h in soup.find_all(level)]
        heads = [(t, i) for t, i in heads if t and t != title]
        if heads:   # each one a link to its heading on the page
            shown = [f"[{md_escape(t)}]({page_url}#{urllib.parse.quote(i)})" if i else md_escape(t) for t, i in heads[:6]]
            lines.append(" · ".join(shown) + (" · …" if len(heads) > 6 else ""))
    if note.name in NAV:
        guide, chapters, i = NAV[note.name]
        if i > 0:
            buttons.append(link_button("← " + chapters[i - 1][0], absolute(notes[chapters[i - 1][1]].url)))
        if i + 1 < len(chapters):
            buttons.append(link_button(chapters[i + 1][0] + " →", absolute(notes[chapters[i + 1][1]].url)))
    # overviews: how many entries they list
    listed = [n for n, (o, _, _) in ENTRY_ORDER.items() if o is note]
    if listed and is_overview(note):
        kind = page_type(notes[listed[0]])
        plural = kind[:-1] + "ies" if kind.endswith("y") else kind + "s"
        lines.append(f"-# {len(listed)} {plural.lower()}")
    # a roleplay channel: a button straight into it
    channel = note.prop("Roleplay Channel")
    channel = channel[0] if isinstance(channel, list) and channel else channel
    m = re.search(r"\[([^\]]+)\]\((https://discord(?:app)?\.com/channels/[^)]+)\)", str(channel or ""))
    if m:
        buttons.append(link_button(m.group(1).replace("\\", ""), m.group(2)))
    # the thumbnail: the note's `_preview` picture if it names one (the maps on the Gazetteer and the
    # Civilizations overview), else a picture of the page's table, its own first picture, or the Covalon logo
    chosen = re.search(r"\[\[([^\]|#]+)", str(note.prop("_preview") or "")) or re.match(r"\s*([^\[\]]+\.\w+)\s*$", str(note.prop("_preview") or ""))
    picture = ((file_url(chosen.group(1).strip()) if chosen else None) or table_shot(note, soup)   # a table's picture: previews.py
               or first_picture(note) or file_url(LOGO))
    shot = None
    image = absolute(picture) if picture else None

    trail = preview_trail(note)
    text = f"## {md_escape(title)}\n" + "\n\n".join(lines)
    top = {"type": 10, "content": shorten_md(text, 1800)}
    head = {"type": 9, "components": [top], "accessory": {"type": 11, "media": {"url": image}}} if image else top
    gallery = [{"type": 12, "items": [{"media": {"url": absolute(shot)}, "description": shorten(title, 200)}]}] if shot else []
    card = {"type": 17, "accent_color": int(PREVIEW_COLOR[1:], 16), "components": [
        head, *gallery,
        {"type": 14, "divider": True, "spacing": 1},
        {"type": 10, "content": "-# " + md_escape(SITE_NAME + (" · " + trail if trail else ""))},
        {"type": 1, "components": buttons[:5]},
    ]}
    payload = json.dumps({"component": card}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    description = shorten(tagline + (" " if tagline and blurb else "") + (blurb if blurb != tagline else ""), 300) or SITE_NAME
    meta = [("og:site_name", SITE_NAME), ("og:type", "website"), ("og:title", title), ("og:description", description),
            ("og:url", page_url)] + ([("og:image", absolute(shot) if shot else image)] if image or shot else [])
    tags = "".join(f'<meta property="{k}" content="{html.escape(v)}">' for k, v in meta)
    tags += (f'<meta name="description" content="{html.escape(description)}">'
             f'<meta name="twitter:card" content="{"summary_large_image" if shot else "summary"}"><meta name="theme-color" content="{PREVIEW_COLOR}">'
             f'<link rel="canonical" href="{html.escape(page_url)}">')
    return f'\n{tags}\n<script id="discord:component-embed" type="application/json">{payload}</script>'


# Pictures of tables for the previews: the build notes each table (its HTML, rows cut to PREVIEW_ROWS) in
# public/_previews.json under a name made from its contents, and previews.py (run after the build, like the
# search index) photographs them in light mode with a headless browser. Unchanged tables keep their picture.
PREVIEW_SHOTS = {}   # site address of the picture -> the table's HTML
PREVIEW_ROWS = 12
PREVIEW_THEME = "light"   # the pictures are taken in light mode (previews.py); part of their names, so a change retakes them
PREVIEW_COLS = 5   # wider tables show their first five columns


def table_shot(note, soup):
    is_table = note.folders and note.folders[-1] == "Tables"
    box = soup.find("table") if is_table else (soup.select_one(".covalon-filterable table") if is_overview(note) or "covalon/district" in note.tags else None)
    if not box:
        return None
    t = BeautifulSoup(str(box), "html.parser").find("table")
    for tr in t.find_all("tr"):
        for cell in tr.find_all(["td", "th"], recursive=False)[PREVIEW_COLS:]:
            cell.decompose()
    body = t.find("tbody") or t
    rows = body.find_all("tr", recursive=False)
    if len(rows) > PREVIEW_ROWS:
        for r in rows[PREVIEW_ROWS:]:
            r.decompose()
        cols = max(len(r.find_all(["td", "th"])) for r in rows[:PREVIEW_ROWS])
        more = BeautifulSoup(f'<tr class="covalon-shot-more"><td colspan="{cols}">…and {len(rows) - PREVIEW_ROWS} more</td></tr>', "html.parser")
        body.append(more)
    for a in t.find_all("a"):   # links look like links, but point nowhere
        a["href"] = "#"
    markup = str(t)
    key = hashlib.sha256((markup + ASSET_VERSIONS["style.css"] + PREVIEW_THEME).encode()).hexdigest()[:16]
    url = f"files/previews/{key}.jpg"
    PREVIEW_SHOTS[url] = markup
    return url


def shorten_md(text, limit):
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "…"


def build_note(note):
    CUR["url"] = note.url
    title = NAV[note.name][1][NAV[note.name][2]][0] if note.name in NAV else SITE_TITLE if note.name == HOME_NOTE else note.title
    style = entry_style(note)
    if style and style["aside"]:   # tagline, text with images floated right, inline properties, properties box at the bottom
        body = (tagline_html(note, style["tagline"]) + '<div class="covalon-entry covalon-entry-aside">\n\n'
                + render_note_aside(note, (), style["inline"], [style["tagline"]] if style["tagline"] else [],
                                    style.get("props_first", False), style.get("beside", False), own_page=True) + '\n\n</div>\n')
    elif style:                    # tagline, properties box, then the text
        hide = [style["tagline"]] if style["tagline"] else []
        body = ('<div class="covalon-entry">\n\n' + tagline_html(note, style["tagline"]) + props_panel(note, hide)
                + "\n\n" + render(note) + '\n\n</div>\n')
    else:
        body = render(note)
    if note.classes:
        body = f'<div class="{" ".join(note.classes)}">\n\n{body.strip()}\n\n</div>\n'
    soup = to_html(body)
    for el in soup.select("[data-last-updated]"):   # e.g. on the home page: the date the site was published
        el.string = nice_date(BUILD_DATE)
    if note.path.relative_to(SRC).parts[0] in SPOILER_FOLDERS:
        spoiler_sections(soup)
    parts = [str(soup)] if style else [props_panel(note), str(soup)]
    pre_title = ""
    if note.name in NAV:   # chapter pages: ← previous / next → above the title, and again at the end
        nav = chapter_nav(note.name)
        pre_title = nav.replace('class="chapter-nav"', 'class="chapter-nav chapter-nav-top"', 1)
        parts = parts + [nav]
    elif note.name in ENTRY_ORDER and len(ENTRY_ORDER[note.name][1]) > 1:   # entry pages: the next item on their overview
        nav = entry_nav(note.name)
        pre_title = nav.replace('class="chapter-nav entry-nav"', 'class="chapter-nav entry-nav chapter-nav-top"', 1)
        parts = parts + [nav]
    content = "\n".join(p for p in parts if p)
    if not is_overview(note):   # overview pages repeat their entries' text, so they're left out of search
        content = f'<div data-pagefind-body>{search_markup(note, title, first_paragraph(soup))}{content}</div>'
    side = ""
    if note.name in GUIDES:   # the whole guide on one page: offer reading it a chapter at a time (right of the title)
        first = next((c for c, (g, ch, i) in NAV.items() if g == note.name and i == 0), None)
        if first:
            side = (f'<a class="guide-paged-link internal-link" href="{href_to(notes[first].url)}" data-pagefind-ignore>'
                    f'{lucide("book-open")}<span>View in paged mode</span></a>')
    write(note.url, page(title, content, toc_html(soup, title), current=note, crumbs=breadcrumbs(note, title) + pre_title, title_side=side,
                         extra_head=preview_head(note, title, soup)))

SEARCH = """Search every page. See [[🔎 How to Search]] for guidance.

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
    (OUT / "assets").mkdir(parents=True)
    for name in enabled:
        if name != SERIF_SNIPPET and (SRC / ".obsidian" / "snippets" / f"{name}.css").exists():
            SNIPPETS.append(name)
    for f in (HERE / "assets").iterdir():
        if f.is_file() and f.suffix != ".css":
            shutil.copy(f, OUT / "assets" / f.name)
    # All the styles in one file, in the order they'd apply in Obsidian: the stand-in for Obsidian's theme,
    # the vault's enabled snippets, callout colours, then the site frame. (@import lines have to come first.)
    parts = [(HERE / "assets" / "base.css").read_text(encoding="utf-8")]
    parts += [(SRC / ".obsidian" / "snippets" / f"{n}.css").read_text(encoding="utf-8") for n in SNIPPETS]
    parts += [callouts_css(), (HERE / "assets" / "site.css").read_text(encoding="utf-8")]
    imports = []
    def keep_import(m):
        imports.append(m.group(0).strip())
        return ""
    body = "\n\n".join(re.sub(r"""(?m)^@import\s+(?:url\([^)]*\)|"[^"]*"|'[^']*')[^;\n]*;[ \t]*$""", keep_import, p) for p in parts)
    (OUT / "assets" / "style.css").write_text("\n".join(imports) + "\n\n" + body, encoding="utf-8")
    # Each asset's link carries a stamp of its contents (style.css?v=3f9a1c), so after a publish browsers
    # fetch the new version straight away instead of using a cached old one.
    serif = SRC / ".obsidian" / "snippets" / f"{SERIF_SNIPPET}.css"
    if serif.exists():
        shutil.copy(serif, OUT / "assets" / serif.name)
    for name in ("style.css", "site.js", "search.js") + ((serif.name,) if serif.exists() else ()):
        digest = hashlib.sha256((OUT / "assets" / name).read_bytes()).hexdigest()[:10]
        ASSET_VERSIONS[name] = f"{name}?v={digest}"

    collect_entry_styles()
    collect_entry_order()
    collect_linked_as()
    file_url(LOGO)
    for n in notes.values():
        build_note(n)
    for src, url in USED_FILES.items():   # the vault's pictures the pages use (big ones made smaller)
        dest = OUT / url
        dest.parent.mkdir(parents=True, exist_ok=True)
        copy_picture(src, dest)
    CUR["url"] = "index.html"
    if HOME_NOTE not in notes:   # no home note in the vault: a plain list of the guides
        write("index.html", page(SITE_TITLE, str(to_html(HOME)), ""))
    CUR["url"] = "search/index.html"
    search_head = ""
    write("search/index.html", page("Advanced Search", str(to_html(SEARCH)), "", extra_head=search_head, search_page=True))
    # the tables to photograph for the link previews (previews.py takes the pictures)
    (OUT / "_previews.json").write_text(json.dumps(PREVIEW_SHOTS, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(notes) + 2} pages to {OUT} ({len(PREVIEW_SHOTS)} table pictures for previews.py)")


if __name__ == "__main__":
    main()
