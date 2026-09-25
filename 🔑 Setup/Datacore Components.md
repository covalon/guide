Shared Datacore components used by the 📍 overview pages. Edit the code below to change how every overview renders its entries.
## CovalonEntries
Lists every note with the given tag: a linked heading, the note's properties, then the full note embedded.

Options: `tag` (required), `inline={["Roleplay Channel"]}` (with `aside`: show those properties as a line of text after the note's text, instead of in the properties box), `tagline="Tagline"` (show that property as a tagline right under each heading, instead of in the properties box), `aside` (a different layout, used for the guilds: heading, the note's text, then its properties, with the note's images floated to the right beside them), `propsFirst` (with `aside`: the properties box comes before the note's text instead of after it, used for the deities and civilizations), `imagesBesideProps` (with `aside`: the note's images sit beside its properties box instead of floating, the box taking 2/3 of the width and the images 1/3, fitted to the box's height; used for the guilds' heraldry), `district` (only locations in that district), `sortBy="title"` (name, ignoring a leading "The"), `sortBy="date"` (or any property name, e.g. `sortBy="Journey Date"`), `heading="h3"`, and `hide={["Some Property"]}` to leave properties out of the panel.

```jsx
// properties never shown: these, and any starting with _ (settings for the website, e.g. _url)
const HIDDEN = new Set(["tags", "aliases", "cssclasses"]);
const label = (k) => k;
// dates (2021-07-17) are shown as "July 17th, 2021"
const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const ordinal = (n) => n + (n % 100 >= 11 && n % 100 <= 13 ? "th" : ({ 1: "st", 2: "nd", 3: "rd" })[n % 10] || "th");
const niceDate = (s) => s.replace(/^(\d{4})-(\d{2})-(\d{2})(?:T[\d:.]+)?$/, (_, y, m, d) => `${MONTHS[+m - 1]} ${ordinal(+d)}, ${y}`);
const show = (v) => (Array.isArray(v) ? v.map(show).join(", ") : niceDate(String(v ?? "")));
const isEmpty = (v) => v === null || v === undefined || v === "" || (Array.isArray(v) && v.length === 0);

function Properties({ page, hide = [] }) {
  const rows = Object.values(page.$frontmatter ?? {}).filter(
    (e) => !HIDDEN.has(e.key.toLowerCase()) && !e.key.startsWith("_") && !hide.includes(e.key) && !isEmpty(e.raw)
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

// aside layout: the note's own text without its images, then its properties, with the images floated right
const IMAGE_LINE = /^\s*!\[.*\]\(.*\)\s*$|^\s*!\[\[[^\]]+\.(png|jpe?g|webp|gif|svg)[^\]]*\]\]\s*$/i;
// shift the note's headings so its top level sits one below the entry's heading (h2 entry -> h3 inside)
function shiftHeadings(text, below) {
  const levels = [...text.matchAll(/^(#{1,6})\s/gm)].map((m) => m[1].length);
  if (!levels.length) return text;
  const delta = below + 1 - Math.min(...levels);
  return text.replace(/^(#{1,6})(?=\s)/gm, (h) => "#".repeat(Math.max(1, Math.min(6, h.length + delta))));
}
function InlineProps({ page, props = [] }) {
  const rows = props
    .map((k) => Object.values(page.$frontmatter ?? {}).find((e) => e.key.toLowerCase() === k.toLowerCase()))
    .filter((e) => e && !isEmpty(e.raw));
  if (!rows.length) return null;
  return rows.map((e) => (
    <p key={e.key} className="covalon-inline-prop">
      <strong>{e.key}:</strong> <dc.Markdown inline content={show(e.raw)} sourcePath={page.$path} />
    </p>
  ));
}

function AsideEntry({ page, hide = [], level = 2, inline = [], propsFirst = false, imagesBesideProps = false, children = null }) {
  const [parts, setParts] = dc.useState({ text: "", images: "" });
  dc.useEffect(() => {
    let live = true;
    const file = dc.app.vault.getAbstractFileByPath(page.$path);
    if (file) dc.app.vault.cachedRead(file).then((raw) => {
      // the note's own bases (and the heading above them) are left out: e.g. a district's "## Locations"
      // table, which the Gazetteer already lists below it
      const body = raw.replace(/^---\n[\s\S]*?\n---\n?/, "").replace(/(^#{1,6} [^\n]*\n+)?^```base\n[\s\S]*?\n```[ \t]*\n?/gm, "");
      const lines = body.split("\n");
      if (live) setParts({
        text: shiftHeadings(lines.filter((l) => !IMAGE_LINE.test(l)).join("\n").trim(), level),
        images: lines.filter((l) => IMAGE_LINE.test(l)).join("\n\n"),
      });
    });
    return () => { live = false; };
  }, [page.$path, page.$mtime]);
  return (
    <div className="covalon-entry-body">
      {parts.images && !imagesBesideProps && <div className="covalon-entry-images"><dc.Markdown content={parts.images} sourcePath={page.$path} /></div>}
      {children /* the entry's heading and tagline: after the images, so the images float from the top of the entry */}
      {propsFirst && <Properties page={page} hide={[...hide, ...inline]} />}
      <dc.Markdown content={parts.text} sourcePath={page.$path} />
      <InlineProps page={page} props={inline} />
      {!propsFirst && !imagesBesideProps && <Properties page={page} hide={[...hide, ...inline]} />}
      {imagesBesideProps && (
        <div className="covalon-props-row">
          <Properties page={page} hide={[...hide, ...inline]} />
          {parts.images && <div className="covalon-props-images"><dc.Markdown content={parts.images} sourcePath={page.$path} /></div>}
        </div>
      )}
    </div>
  );
}

function Tagline({ page, prop }) {
  const entry = prop && Object.values(page.$frontmatter ?? {}).find((e) => e.key.toLowerCase() === prop.toLowerCase());
  if (!entry || isEmpty(entry.raw)) return null;
  return <div className="covalon-tagline"><dc.Markdown inline content={show(entry.raw)} sourcePath={page.$path} /></div>;
}

function CovalonEntries({ tag, district, sortBy = "name", heading = "h2", hide = [], aside = false, propsFirst = false, imagesBesideProps = false, tagline, inline = [] }) {
  if (tagline) hide = [...hide, tagline];
  const pages = dc.useQuery(`@page and #${tag}`);
  let entries = [...pages];
  if (district) entries = entries.filter((p) => districtOf(p) === district);
  const sortProp = sortBy === "date" ? "Date" : sortBy;
  const title = (p) => p.$name.replace(/^(the )?(kingdom of )?/i, "");
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
        aside ? (
          <div key={p.$path} className="covalon-entry covalon-entry-aside">
            <AsideEntry page={p} hide={hide} inline={inline} propsFirst={propsFirst} imagesBesideProps={imagesBesideProps} level={Number(heading.slice(1)) || 2}>
              <H><dc.Link link={p.$link} /></H>
              <Tagline page={p} prop={tagline} />
            </AsideEntry>
          </div>
        ) : (
          <div key={p.$path} className="covalon-entry">
            <H><dc.Link link={p.$link} /></H>
            <Tagline page={p} prop={tagline} />
            <Properties page={p} hide={hide} />
            <dc.LinkEmbed link={p.$link} />
          </div>
        )
      ))}
    </div>
  );
}

// One note in the aside layout (its text, its images floated right, its properties box), without a heading.
// Used for the districts on the Gazetteer: <CovalonNote name="📍 City District" propsFirst />
function CovalonNote({ name, tag = "covalon/district", inline = [], propsFirst = false }) {
  const pages = dc.useQuery(`@page and #${tag}`);
  const page = pages.find((p) => p.$name === name);
  if (!page) return null;
  return <div className="covalon-entry-aside covalon-note"><AsideEntry page={page} inline={inline} propsFirst={propsFirst} /></div>;
}

// A bulleted list of the notes with a tag, optionally only those whose property `where` is `is`, each followed
// by another property in brackets. The Expedition Districts page lists the civilizations this way:
// <CovalonList tag="covalon/civilization" where="Covalon Status" is="district" after="Roleplay Channel" />
function CovalonList({ tag, where, is, after }) {
  const pages = dc.useQuery(`@page and #${tag}`);
  const prop = (p, k) => Object.values(p.$frontmatter ?? {}).find((e) => e.key.toLowerCase() === String(k).toLowerCase());
  const title = (p) => p.$name.replace(/^(the )?(kingdom of )?/i, "");
  const rows = pages
    .filter((p) => !where || String(prop(p, where)?.raw ?? "").trim().toLowerCase() === String(is ?? "").trim().toLowerCase())
    .sort((a, b) => title(a).localeCompare(title(b)));
  if (!rows.length) return null;
  const md = rows.map((p) => {
    const extra = after && prop(p, after);
    return `- [[${p.$name}]]` + (extra && !isEmpty(extra.raw) ? ` (${show(extra.raw)})` : "");
  }).join("\n");
  return <dc.Markdown content={md} sourcePath={rows[0].$path} />;
}

return { CovalonEntries, CovalonNote, CovalonList };
```
## CovalonList
A bulleted list of notes with a tag, each linked, sorted by name (ignoring a leading "The"). Options: `tag` (required), `where` and `is` (only the notes whose property `where` has the value `is`, e.g. `where="Covalon Status" is="district"`), and `after` (a property shown in brackets after each name, e.g. `after="Roleplay Channel"`). The Expedition Districts and Outside Covalon page uses it to list the civilizations that are districts and camps. It's part of the CovalonEntries code block above.

## CovalonNote
One note shown in the `aside` layout of `CovalonEntries` (its text, its images floated to the right, then its properties box), without a heading of its own. The Gazetteer uses it for each district: `<CovalonNote name="📍 City District" propsFirst />`. Options: `tag` (default `covalon/district`), `inline`, and `propsFirst` (the properties box before the note's text), as for `CovalonEntries`. It's part of the CovalonEntries code block above.

## MissionOverview
Every expedition's missions in one table (each named after its expedition, e.g. "Ikouga A: Retame the Island"),, read straight from the expedition notes: each `### Mission X` heading under `## Missions` (with its name after a colon, if it has one) and the text underneath it as the summary. Edit a mission on its expedition note and the table follows. Expeditions are listed in journey order.

```jsx
function missionsIn(text) {
  // the expedition note's "## Missions" table: | A: Mission name | summary |
  const missions = [];
  let inMissions = false;
  for (const line of text.split("\n")) {
    if (/^## /.test(line)) { inMissions = /^## Missions\s*$/.test(line); continue; }
    if (!inMissions || !line.trim().startsWith("|")) continue;
    const cells = line.trim().replace(/^\||\|$/g, "").split(/(?<!\\)\|/).map((c) => c.trim());
    const m = (cells[0] || "").match(/^([A-Z])(?::\s*(.+))?$/);
    if (!m) continue;   // the header and divider rows
    missions.push({ letter: m[1], name: (m[2] ?? "").trim(), summary: (cells[1] || "").replace(/\\\|/g, "|") });
  }
  return missions;
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
  // one table of every mission, named after its expedition: "Ikouga A: Retame the Island"
  return (
    <table className="covalon-mission-overview">
      <thead>
        <tr><th>Mission</th><th>Summary</th></tr>
      </thead>
      <tbody>
        {rows.flatMap(({ page, missions }) =>
          missions.map((m) => (
            <tr key={page.$path + m.letter}>
              <td>{page.$name.replace(/ Expedition$/, "")} {m.letter}{m.name ? `: ${m.name}` : ""}</td>
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
