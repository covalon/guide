<%*
const baseFolder = "Guilds";

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
  - covalon/guild
Headquarters:
Leader:
Members:
  -
Membership Requirements:
Goals:
Values:
Anathema:
_published: false
---
SUMMARY

`![[IMAGE|GUILDNAME Heraldry. Designed by CREDIT.]]`
