<%*
const civFolder = "Civilizations";
const logFolder = "Expeditions";

// 1. Pick the civilization (Esc cancels the whole template)
const civs = tp.app.vault.getMarkdownFiles()
  .filter(f => f.path.startsWith(civFolder + "/") && !f.basename.includes(`📍`));
const civ = await tp.system.suggester(
  civs.map(f => f.basename), civs, true, "Which civilization?"
)

// 2. Name and file the log
const name = await tp.system.prompt("Expedition log name?", civ.basename);
await tp.file.move(`${logFolder}/${name} Expedition`);

// 3. Add a link to this log inside the civilization note
const link = `[[${name} Expedition]]`;
await tp.app.fileManager.processFrontMatter(civ, fm => {
  fm["Expedition Log"] = fm["Expedition Log"] ?? link;
  fm["Roleplay Channel"] = fm["Roleplay Channel"] ?? [];
});

await new Promise(r => setTimeout(r, 200));   // let the move/rename settle

// Show in File Explorer
const file = tp.app.vault.getAbstractFileByPath(tp.file.path(true));
const explorer = tp.app.workspace.getLeavesOfType("file-explorer")[0]?.view;
explorer?.revealInFolder(file);
-%>
---
Tags:
  - covalon/expedition
Civilization: "[[<% civ.basename %>]]"
Soul Seed:
Finale:
Journey Date:
Finale First Cleared:
_published: false
---
Expedition to [[<% civ.basename %>]].
## Expedition Log
> [!heroes|right] Heroes of <% name %>
> The following characters were the first to defeat ???
>
> -

SUMMARY

## Base Camp
*Image to come.*

## Missions
| Mission | Summary |
| :-- | :-- |
| A: NAME | TEXT |
| B: NAME | TEXT |
| C: NAME | TEXT |

## Finale
**Boss:** ???

*Summary to come.*

## Soul Seed
Completing the finale unlocks the [||??? aspect||](https://2e.aonprd.com/Relics.aspx) for your Soul Seed (see [[Chapter 3 - Covalon Gameplay#Table 3-2 Aspect Category Unlocks|Table 3-2]] and [[Chapter 3 - Covalon Gameplay#Table 3-3 Soul Seed Upgrade Unlocks|3-3]] in the [[Chapter 3 - Covalon Gameplay#Soul Seeds|Player's Guide]]).
