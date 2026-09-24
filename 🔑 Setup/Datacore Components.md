Shared Datacore components used by the 📍 overview pages. Edit the code below to change how every overview renders its entries.
## CovalonEntries
Lists every note with the given tag: a linked heading, the note's properties, then the full note embedded.

Options: `tag` (required), `district` (only locations in that district), `sortBy="title"` (name, ignoring a leading "The"), `sortBy="date"` (or any property name, e.g. `sortBy="Journey Date"`), `heading="h3"`, and `hide={["Some Property"]}` to leave properties out of the panel.

```jsx
const HIDDEN = new Set(["tags", "aliases", "cssclasses"]);
const label = (k) => k;
const show = (v) => (Array.isArray(v) ? v.map(show).join(", ") : String(v ?? ""));
const isEmpty = (v) => v === null || v === undefined || v === "" || (Array.isArray(v) && v.length === 0);

function Properties({ page, hide = [] }) {
  const rows = Object.values(page.$frontmatter ?? {}).filter(
    (e) => !HIDDEN.has(e.key.toLowerCase()) && !hide.includes(e.key) && !isEmpty(e.raw)
  );
  if (!rows.length) return null;
  return (
    <div className="covalon-props">
      {rows.map((e) => (
        <div className="covalon-prop" key={e.key}>
          <span className="covalon-prop-key">{label(e.key)}</span>
          <dc.Markdown className="covalon-prop-value" inline content={show(e.raw)} sourcePath={page.$path} />
        </div>
      ))}
    </div>
  );
}

// District may be plain text or a link like [[📍 Covalon Gazetteer#Market District|Market District]]
function districtOf(page) {
  const entry = Object.values(page.$frontmatter ?? {}).find((e) => e.key.toLowerCase() === "district");
  const raw = String(entry?.raw ?? "");
  const m = raw.match(/\[\[[^\]#|]*#([^\]|]+)/) || raw.match(/\[\[[^\]|]*\|([^\]]+)\]\]/) || raw.match(/\[\[([^\]|#]+)\]\]/);
  return (m ? m[1] : raw).trim();
}

function CovalonEntries({ tag, district, sortBy = "name", heading = "h2", hide = [] }) {
  const pages = dc.useQuery(`@page and #${tag}`);
  let entries = [...pages];
  if (district) entries = entries.filter((p) => districtOf(p) === district);
  const sortProp = sortBy === "date" ? "Date" : sortBy;
  const title = (p) => p.$name.replace(/^the /i, "");
  entries.sort(
    sortBy === "name"
      ? (a, b) => a.$name.localeCompare(b.$name)
      : sortBy === "title"
      ? (a, b) => title(a).localeCompare(title(b))
      : (a, b) => String(a.value(sortProp) ?? "").localeCompare(String(b.value(sortProp) ?? ""))
  );
  const H = heading;
  return (
    <div className="covalon-entries">
      {entries.map((p) => (
        <div key={p.$path} className="covalon-entry">
          <H><dc.Link link={p.$link} /></H>
          <Properties page={p} hide={hide} />
          <dc.LinkEmbed link={p.$link} />
        </div>
      ))}
    </div>
  );
}

return { CovalonEntries };
```
## MissionOverview
A table of every expedition's missions, read straight from the expedition notes: each `### Mission X` heading under `## Missions` (with its name after a colon, if it has one) and the text underneath it as the summary. Edit a mission on its expedition note and the table follows. Expeditions are listed in journey order.

```jsx
function missionsIn(text) {
  const missions = [];
  const lines = text.split("\n");
  let cur = null;
  let inMissions = false;
  for (const line of lines) {
    if (/^## /.test(line)) { inMissions = /^## Missions\s*$/.test(line); cur = null; continue; }
    if (!inMissions) continue;
    const m = line.match(/^### Mission ([A-Z])(?::\s*(.+))?\s*$/);
    if (m) { cur = { letter: m[1], name: (m[2] ?? "").trim(), summary: [] }; missions.push(cur); continue; }
    if (/^#{1,3} /.test(line)) { cur = null; continue; }
    if (cur) cur.summary.push(line);
  }
  return missions.map((m) => ({ ...m, summary: m.summary.join("\n").trim() }));
}

function MissionOverview({ tag = "covalon/expedition" }) {
  const pages = dc.useQuery(`@page and #${tag}`);
  const [rows, setRows] = dc.useState([]);
  const stamp = pages.map((p) => p.$path + p.$mtime).join("|");
  dc.useEffect(() => {
    let live = true;
    const sorted = [...pages].sort((a, b) =>
      String(a.value("Journey Date") ?? "").localeCompare(String(b.value("Journey Date") ?? "")));
    Promise.all(sorted.map(async (p) => {
      const file = dc.app.vault.getAbstractFileByPath(p.$path);
      const text = file ? await dc.app.vault.cachedRead(file) : "";
      return { page: p, missions: missionsIn(text) };
    })).then((r) => { if (live) setRows(r); });
    return () => { live = false; };
  }, [stamp]);
  return (
    <table className="covalon-mission-overview">
      <thead>
        <tr><th>Expedition</th><th>Mission</th><th>Summary</th></tr>
      </thead>
      <tbody>
        {rows.flatMap(({ page, missions }) =>
          missions.map((m, i) => (
            <tr key={page.$path + m.letter}>
              {i === 0 && (
                <td rowSpan={missions.length}>
                  <dc.Markdown content={`[[${page.$name}|${page.$name.replace(/ Expedition$/, "")}]]`} sourcePath={page.$path} inline />
                </td>
              )}
              <td>
                <dc.Markdown content={`[[${page.$name}#${m.name ? `Mission ${m.letter} ${m.name}` : `Mission ${m.letter}`}|${m.letter}${m.name ? `: ${m.name}` : ""}]]`} sourcePath={page.$path} inline />
              </td>
              <td><dc.Markdown content={m.summary} sourcePath={page.$path} /></td>
            </tr>
          ))
        )}
      </tbody>
    </table>
  );
}

return { MissionOverview };
```
