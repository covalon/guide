<%*
const cityFolder = "City of Covalon";

// 1. Pick the district (Esc cancels the whole template)
const districts = tp.app.vault.getMarkdownFiles()
  .filter(f => f.path.startsWith(cityFolder + "/") && f.basename.includes(`📍`) && !f.basename.includes('City of Covalon'));
const district = await tp.system.suggester(
  districts.map(f => f.basename), districts, true, "Which district?"
)

// 2. Name and file the log
const name = await tp.system.prompt(`Name (can't include * " \ / < > : | ?)`);
await tp.file.move(`${district.parent.path}/${name}`);

await new Promise(r => setTimeout(r, 200));   // let the move/rename settle

// Show in File Explorer
const file = tp.app.vault.getAbstractFileByPath(tp.file.path(true));
const explorer = tp.app.workspace.getLeavesOfType("file-explorer")[0]?.view;
explorer?.revealInFolder(file);
-%>
---
Tags:
  - covalon/location
District: '[[<%district.basename%>]]'
Guild Headquarters of:
  -
Player Owned:
_published: false
---
SUMMARY

`![[IMAGE|CAPTION. Designed by CREDIT.]]`
