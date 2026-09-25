An overview of every callout Obsidian supports. The guide currently uses **note**, **info**, **tip** and **warning**.

Write a callout as a quote that starts with the type in brackets. The title after it is optional:

```markdown
> [!note] Optional Title
> The callout's text goes here.
```

To leave out the title, add `|notitle` after the type (see below).

Add `+` or `-` after the type to make it foldable, open or closed by default: `> [!note]+ Title` or `> [!note]- Title`.

## Types

Every callout Callout Manager knows about: Obsidian's built-in ones, any from snippets, and new ones made in the plugin. The list updates when this page is reopened. To change a color or icon or make a brand new callout, use Settings → Callout Manager.

```datacorejsx
// What each callout is used for in the guide (shown under its name when set)

function title(id) {
  return id.charAt(0).toUpperCase() + id.slice(1).toLowerCase().replace(/-+/g, " ");
}

// Same order as the Callout Manager settings list: colour first (coloured before gray,
// then by hue, highest first), then name
function hsv(colour) {
  const str = String(colour ?? "").trim();
  let rgb = null;
  const hex = str.match(/^#([0-9a-f]{3}|[0-9a-f]{6})$/i);
  if (hex) {
    const h = hex[1].length === 3 ? hex[1].replace(/./g, "$&$&") : hex[1];
    rgb = [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
  } else {
    const n = str.match(/[\d.]+/g);
    if (n && n.length >= 3) rgb = n.slice(0, 3).map(Number);
  }
  if (!rgb) return null;
  const [r, g, b] = rgb.map((v) => v / 255);
  const max = Math.max(r, g, b), min = Math.min(r, g, b), d = max - min;
  let h = 0;
  if (d) h = max === r ? (60 * ((g - b) / d) + 360) % 360 : max === g ? 60 * ((b - r) / d) + 120 : 60 * ((r - g) / d) + 240;
  return { h, s: max ? (d / max) * 100 : 0, v: max * 100 };
}

function byColour(a, b) {
  if (!a.hsv !== !b.hsv) return a.hsv ? -1 : 1;
  if (!a.hsv) return 0;
  if ((a.hsv.s > 0) !== (b.hsv.s > 0)) return a.hsv.s > 0 ? -1 : 1;
  const dh = b.hsv.h - a.hsv.h;
  if (Math.abs(dh) > 2) return dh;
  return (b.hsv.s + b.hsv.v) - (a.hsv.s + a.hsv.v);
}

return function View() {
  const cm = dc.app.plugins.plugins["callout-manager"];
  if (!cm?.callouts) return <p>Turn on the Callout Manager plugin to see the list of callouts.</p>;
  const changed = cm.settings?.callouts?.settings ?? {};
  // layout callouts (their own sections below) are left out of this list
  const LAYOUT = ["columns", "statblock", "clear"];
  // one-off callouts with their own icons (the Brawls page's Monster Mash tables) go at the bottom, in this order
  const LAST = ["dino", "fey", "dragon"];
  const last = (c) => LAST.indexOf(c.id) + 1;
  const all = [...cm.callouts.values()]
    .filter((c) => !LAYOUT.includes(c.id))
    .map((c) => ({ c, hsv: hsv(c.color) }))
    .sort((a, b) => last(a.c) - last(b.c) || (last(a.c) ? 0 : byColour(a, b)) || a.c.id.localeCompare(b.c.id))
    .map(({ c }) => c);
  // Aliases (e.g. warning / caution / attention) share a colour and icon: show one callout per
  // group, named after Obsidian's main type when there is one, with the others listed under it
  const MAIN = ["note", "abstract", "info", "todo", "tip", "success", "question", "warning",
    "failure", "danger", "bug", "example", "quote"];
  const groups = [];
  const byLook = new Map();
  for (const c of all) {
    const look = `${String(c.color).replace(/\s+/g, "")}|${c.icon}`;
    if (!byLook.has(look)) { byLook.set(look, []); groups.push(byLook.get(look)); }
    byLook.get(look).push(c);
  }
  const pick = (g) => g.find((c) => MAIN.includes(c.id)) ?? g[0];
  const code = (id) => `\`[!${id}]\``;

  // one Markdown block per callout: inside a single block the callouts sit flush against each other
  return (
    <div className="covalon-callout-list" style={{ display: "flex", flexDirection: "column", gap: "1em" }}>
      {groups.map((g) => {
        const main = pick(g);
        const aliases = g.filter((c) => c !== main).map((c) => code(c.id));
        const lines = [`> [!${main.id}] ${title(main.id)}`, `> ${[code(main.id), ...aliases].join(" ･ ")}`];
        return <dc.Markdown key={main.id} sourcePath={dc.currentPath()} content={lines.join("\n")} />;
      })}
    </div>
  );
};
```

## Without a Title

Add `|notitle` after the type to hide the whole title bar (title, icon and band), so the text starts at the top. It combines with floats, e.g. `[!info|right notitle]`.

```markdown
> [!note|notitle]
> Just the text, no title bar.
```

> [!note|notitle]
> Just the text, no title bar.

## Foldable

> [!note]+ Open by Default
> Click the title to collapse this one.

> [!note]- Closed by Default
> This text stays hidden until the title is clicked.

## Nested

> [!info] Callouts Can Contain Other Callouts
> > [!warning] Like This
> > Indent with an extra `>`.

## Floating Callouts

Add `|right` or `|left` after the type to float a callout beside the text, like a sidebar. 

Floats wrap around in reading view and on the site; the editing view makes them take up the full space to prevent some typical Obsidian glitching.

> [!heroes|right] Floated Right
> Used for the Heroes sidebars on events and expeditions.
> - Hero One
> - Hero Two
> - Hero Three

This paragraph flows around the callout on the right. Put the float directly before the text it should sit beside, so the two line up.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.


> [!example|left] Floated Left
> The same thing on the other side.

This paragraph flows around the callout on the left.

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

To make something start below a floated callout instead of beside it, put a line with just `> [!clear]` before it. It's invisible in reading view and on the site; in the editing view it shows as a thin dashed line.

```markdown
> [!heroes|right] Heroes of Somewhere
> - Hero One

A paragraph beside the sidebar.

> [!clear]

This paragraph starts below the sidebar.
```

## Columns

A `[!columns]` callout lays out the callouts inside it side by side, like the three Brawl tables. The outer callout is invisible: each callout inside it becomes one box. Put a line with just `>` between the boxes. The boxes share the width evenly and wrap onto new rows on narrow screens.

```markdown
> [!columns|notitle]
> > [!note|notitle]
> > #### First Box
> > Text or a table…
>
> > [!note|notitle]
> > #### Second Box
> > Text or a table…
```

> [!columns|notitle]
> > [!note|notitle]
> > #### First Box
> > Headings inside the boxes still show in the outline.
>
> > [!note|notitle]
> > #### Second Box
> > Any callout type works for the boxes.
>
> > [!note|notitle]
> > #### Third Box
> > | Number | Name |
> > | :---: | :---: |
> > | 1 | Example |
> > | 2 | Example |

## Statblocks

A `[!statblock]` callout is styled like a PF2e activity, spell or ritual block. 

Its first heading is the title, and `*text*` in the heading sits on the right. 

Inline code is a trait: \`Trait\`.
A highlight is the rarity: `==Uncommon==`, `==**Rare**==` or `==*Unique*==`. 

Leave a blank `>` line around each `---`. After a rule, lines that start with a bold label get a hanging indent.

```markdown
> [!statblock]
> #### Cure a Curse *Activity*
> ==Uncommon== `Covalon` `Exploration`
> **Frequency** once per day; **Cost** 40 gp
>
> ---
>
> You visit the chapel to remove a curse.
>
> **Success** The curse is removed.
```

> [!statblock]
> #### Cure a Curse *Activity*
> ==Uncommon== `Covalon` `Exploration`
>
> **Frequency** once per day; **Cost** 40 gp
>
> ---
>
> You visit the chapel to remove a curse. The church automatically counteracts one curse afflicting your character or an item your character possesses.
>
> **Success** The curse is removed.
>
> **Failure** The curse remains.
