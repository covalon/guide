<%*
const baseFolder = "Adventure Types";

// 2. Name and file the log
const name = await tp.system.prompt(`Name (can't include * " \ / < > : | ?)`);
await tp.file.move(`${baseFolder}/${name}`);

await new Promise(r => setTimeout(r, 200));   // let the move/rename settle

// Show in File Explorer
const file = tp.app.vault.getAbstractFileByPath(tp.file.path(true));
const explorer = tp.app.workspace.getLeavesOfType("file-explorer")[0]?.view;
explorer?.revealInFolder(file);
-%>
---
Tags:
  - covalon/adventure-type
_order:
Duration: x hours
Description:
T1–T3 EXP: "500"
T4–T5 EXP: "250"
_published: false
---
## For Players
text here

## For GMs
text here