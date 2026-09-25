Automatically generated ToC for each of the automatic pages (the one page guides and the compendium overviews). Drafts will not show up here. Everything that isn't part of a generated page is listed at the end. 

Click any line to open that note or heading; click the arrow beside a page's name (or the empty part of its line) to fold it open or shut. 

```datacorejsx
// ---------------------------------------------------------------- helpers
const natural = (a, b) => String(a).localeCompare(String(b), undefined, { numeric: true, sensitivity: "base" });
const sortName = (s) => s.replace(/^(the )?(kingdom of )?/i, "");
const prop = (p, k) => Object.values(p.$frontmatter ?? {}).find((e) => e.key.toLowerCase() === String(k).toLowerCase())?.raw;
const isPublished = (p) => {   // no _published, or ticked: published; unticked or blank: a draft
  const e = Object.values(p.$frontmatter ?? {}).find((x) => x.key === "_published");
  return !e || e.raw === true || String(e.raw).trim().toLowerCase() === "true";
};
const districtOf = (p) => {
  const raw = String(prop(p, "district") ?? "");
  const m = raw.match(/\[\[[^\]#|]*#([^\]|]+)/) || raw.match(/\[\[[^\]|]*\|([^\]]+)\]\]/) || raw.match(/\[\[([^\]|#]+)\]\]/);
  return (m ? m[1] : raw).trim();
};
const jsx = (src, key) => (src.match(new RegExp(`${key}="([^"]*)"`)) || [])[1];
const headingsOf = (p) => {
  const file = dc.app.vault.getAbstractFileByPath(p.$path);
  return (file && dc.app.metadataCache.getFileCache(file)?.headings) || [];
};
const folderOf = (p) => p.$path.split("/").slice(0, -1).join("/");

// a note's headings, nested: [{ text, path, heading, children }]
function nestHeadings(p) {
  const root = { level: 0, children: [] }, stack = [root];
  for (const hd of headingsOf(p)) {
    const node = { text: hd.heading, path: p.$path, heading: hd.heading, level: hd.level, children: [] };
    while (stack.length > 1 && stack[stack.length - 1].level >= hd.level) stack.pop();
    stack[stack.length - 1].children.push(node);
    stack.push(node);
  }
  return root.children;
}
const entryNode = (p, text) => ({ text: text ?? p.$name, path: p.$path, children: nestHeadings(p) });

// the entries a <CovalonEntries … /> block lists, in its order
function entriesFor(src, pages) {
  const tag = jsx(src, "tag"), district = jsx(src, "district"), sortBy = jsx(src, "sortBy") || "name";
  let list = pages.filter((p) => (p.$tags ?? []).some((t) => t === "#" + tag || t === tag));
  if (district) list = list.filter((p) => districtOf(p) === district);
  const key = sortBy === "name" ? (p) => p.$name
    : sortBy === "title" ? (p) => sortName(p.$name)
    : (p) => prop(p, sortBy === "date" ? "Date" : sortBy) ?? "";
  return list.sort((a, b) => natural(key(a), key(b)));
}

// ---------------------------------------------------------------- one generated page's contents
function guideContents(guide, pages) {   // <CovalonGuide />: the chapters in its folder, in number order
  return pages
    .map((p) => ({ p, m: p.$name.match(/^Chapter (\d+) - (.+)$/) }))
    .filter(({ p, m }) => m && folderOf(p) === folderOf(guide))
    .sort((a, b) => Number(a.m[1]) - Number(b.m[1]))
    .map(({ p, m }) => entryNode(p, m[1] === "0" ? "Introduction" : `Chapter ${Number(m[1])}: ${m[2]}`));
}

function overviewContents(overview, text, pages, byName) {   // its own headings, with its entries under them
  const root = { level: 0, children: [] }, stack = [root];
  const add = (node) => stack[stack.length - 1].children.push(node);
  const lines = text.replace(/^---\n[\s\S]*?\n---\n?/, "").split("\n");
  for (let i = 0; i < lines.length; i++) {
    const fence = lines[i].match(/^```(\w+)/);
    if (fence) {
      let j = i + 1;
      while (j < lines.length && !lines[j].startsWith("```")) j++;
      const src = lines.slice(i + 1, j).join("\n");
      if (fence[1] === "datacorejsx") {
        const one = src.match(/<CovalonNote\b[^>]*\bname="([^"]+)"/);
        if (one) {
          const p = byName[one[1]];
          const here = stack[stack.length - 1];
          if (p && here.heading && here.heading === p.$name.replace(/^📍\s*/, "")) {
            // a district under its own heading ("## City District"): the heading line is the district's note
            Object.assign(here, { path: p.$path, heading: undefined });
            here.children.push(...nestHeadings(p));
          } else if (p) add(entryNode(p, p.$name.replace(/^📍\s*/, "")));
        }
        else if (src.includes("<CovalonEntries")) entriesFor(src, pages).forEach((p) => add(entryNode(p)));
      }
      i = j;
      continue;
    }
    const hd = lines[i].match(/^(#{1,6})\s+(.+?)\s*#*$/);
    if (hd) {
      const node = { text: hd[2], path: overview.$path, heading: hd[2], level: hd[1].length, children: [] };
      while (stack.length > 1 && stack[stack.length - 1].level >= node.level) stack.pop();
      add(node);
      stack.push(node);
    }
  }
  return root.children;
}

// ---------------------------------------------------------------- drawing
const STYLE = `
.covalon-vault-map { line-height: 1.5; }
.covalon-vault-map ul { margin: 0.1em 0 0.1em 0.3em !important; padding-left: 1em !important; border-left: 1px solid var(--background-modifier-border); list-style: none; }
.covalon-vault-map li::before, .covalon-vault-map li::marker { content: none !important; display: none !important; }   /* the lines show the levels instead of bullets */
.covalon-vault-map li { margin: 0 !important; }
.covalon-vault-map a.internal-link { color: var(--text-muted); text-decoration: none; }
.covalon-vault-map a.internal-link:hover { color: var(--link-color-hover); text-decoration: underline; }
.covalon-vault-map .page { margin: 0.9em 0 0.2em; font-size: 1.15em; font-weight: var(--font-semibold); cursor: pointer; list-style: none; display: flex; align-items: baseline; gap: 0.4em; }
.covalon-vault-map summary.page::-webkit-details-marker { display: none; }
.covalon-vault-map summary.page::before { content: "›"; display: inline-block; width: 0.7em; flex: none; color: var(--text-faint); transition: transform 120ms; }
.covalon-vault-map details[open] > summary.page::before { transform: rotate(90deg); }
.covalon-vault-map .buttons { margin: 0.4em 0; }
.covalon-vault-map .buttons button { font-size: var(--font-ui-small); margin-right: 0.4em; }
.covalon-vault-map .page a.internal-link { color: var(--text-normal); }
.covalon-vault-map .count { color: var(--text-faint); font-size: var(--font-ui-small); }
`;
const linkTo = (node) => (node.heading ? dc.headerLink(node.path, node.heading) : dc.fileLink(node.path)).withDisplay(node.text);

function Tree({ nodes }) {
  if (!nodes.length) return null;
  return (
    <ul>
      {nodes.map((n, i) => (
        <li key={i}><dc.Link link={linkTo(n)} /><Tree nodes={n.children} /></li>
      ))}
    </ul>
  );
}

return function View() {
  const pages = dc.useQuery("@page").filter(isPublished);
  const byName = Object.fromEntries(pages.map((p) => [p.$name, p]));
  // the generated pages: the pinned notes with a <CovalonGuide /> or <CovalonEntries /> / <CovalonNote /> block
  const pinned = pages.filter((p) => p.$name.startsWith("📍")).sort((a, b) => natural(a.$path, b.$path));
  const [texts, setTexts] = dc.useState({});
  const [all, setAll] = dc.useState(false);      // each generated page starts folded
  const [version, setVersion] = dc.useState(0);  // re-draws, so "Fold all" also shuts what was opened by hand
  const stamp = pinned.map((p) => p.$path + p.$mtime).join("|");
  dc.useEffect(() => {
    let live = true;
    Promise.all(pinned.map((p) => {
      const f = dc.app.vault.getAbstractFileByPath(p.$path);
      return f ? dc.app.vault.cachedRead(f).then((t) => [p.$path, t]) : [p.$path, ""];
    })).then((rows) => { if (live) setTexts(Object.fromEntries(rows)); });
    return () => { live = false; };
  }, [stamp]);

  const sections = [], shown = new Set();
  const mark = (nodes) => nodes.forEach((n) => { if (!n.heading) shown.add(n.path); mark(n.children); });
  for (const p of pinned) {
    const text = texts[p.$path] ?? "";
    let nodes = null;
    if (text.includes("<CovalonGuide")) nodes = guideContents(p, pages);
    else if (/<Covalon(Entries|Note)\b/.test(text)) nodes = overviewContents(p, text, pages, byName);
    if (!nodes) continue;
    shown.add(p.$path);
    mark(nodes);
    sections.push({ page: p, nodes });
  }
  // everything else, by folder
  const rest = pages.filter((p) => !shown.has(p.$path)).sort((a, b) => natural(a.$path, b.$path));
  const folders = {};
  for (const p of rest) (folders[folderOf(p) || "(top of the vault)"] ??= []).push(p);

  return (
    <div className="covalon-vault-map">
      <style>{STYLE}</style>
      <div className="count">{sections.length} generated pages · {pages.length} notes</div>
      <div className="buttons">
        <button onClick={() => { setAll(true); setVersion(version + 1); }}>Unfold all</button>
        <button onClick={() => { setAll(false); setVersion(version + 1); }}>Fold all</button>
      </div>
      <div key={version}>
        {sections.map(({ page, nodes }) => (
          <details key={page.$path} open={all}>
            <summary className="page"><span onClick={(e) => e.preventDefault()}><dc.Link link={dc.fileLink(page.$path).withDisplay(page.$name)} /></span></summary>
            <Tree nodes={nodes} />
          </details>
        ))}
        <details open={all}>
          <summary className="page">Everything else</summary>
          <ul>
            {Object.keys(folders).sort(natural).map((f) => (
              <li key={f}>{f}<Tree nodes={folders[f].map((p) => entryNode(p))} /></li>
            ))}
          </ul>
        </details>
      </div>
    </div>
  );
};
```
