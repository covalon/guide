
This vault **is** the Covalon guide. Everything you see at [covalon.github.io/guide](https://covalon.github.io/guide/) is made from the notes in this vault. You edit notes in Obsidian, send your changes to GitHub, and the website updates itself a few minutes later.

> [!tip] The short version
> 1. **Get the latest** (GitHub Desktop → *Fetch origin*, then *Pull origin*).
> 2. **Edit in Obsidian.**
> 3. **Send it** (GitHub Desktop → write a short summary → *Commit to main* → *Push origin*).
> 4. Wait a few minutes, then check the website.

## First-time setup
You only do this once per computer.

1. **Install [Obsidian](https://obsidian.md/)** and **[GitHub Desktop](https://desktop.github.com/)**.
2. **Sign in to GitHub Desktop** with your GitHub account.
3. In GitHub Desktop, choose **File → Clone repository**, pick `covalon/guide`, and choose where to keep it (e.g. your Documents folder).
4. In Obsidian, choose **Open folder as vault** and pick the folder you just cloned.
5. When Obsidian asks whether to trust the vault's plugins, choose **Trust author and enable plugins**. The guide needs them (Datacore draws the lists, Image Converter lines up the pictures, Inline spoilers shows `||spoilers||`).
6. Turn on the guide's styles: **Settings → Appearance → CSS snippets**, and switch on: `custom`, `image-captions` and `parchment-background`.  These will adjust Obsidian to look as close as possible to the live site. You can also optionally set light or dark mode.
   (Leave *original-guide-fonts* off unless you like the serif look. It's the "Serif" font option on the website.) This is a personal setting, like your theme, so it isn't shared through GitHub.

> [!warning] Pictures
> Pictures are stored with *Git LFS*. GitHub Desktop handles this for you. If it ever asks to "initialize Git LFS", say **yes**.

## Every time you edit
**Before you start:** open GitHub Desktop and click **Fetch origin** (then **Pull origin** if it appears). This gets everyone else's changes first, so you don't edit an old copy.

**When you're done making your edits:**

1. Open GitHub Desktop. Your changed notes are listed on the left.
2. At the bottom left, write a short **Summary** of what you changed, like *"Added the Ember Guild"* or *"Fixed typos in Chapter 3"*.
3. Click **Commit to main**, then **Push origin** at the top.
4. The website rebuilds itself. It takes about 3–5 minutes. You can watch it on GitHub under the repository's **Actions** tab. A green tick means it's live; a red cross means something went wrong. 
   *(Izzy gets an email when that happens but always good to ping her anyways.)*
## Reading, editing and source views
Obsidian can show a note in three ways. Switching between them is a local thing - your view doesn't impact the site.

| View                       | What it's for                                                                                                                                                      | How to get there                                                                                                                                                |
| :------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Reading view**           | Looks like the website: pictures, tables, the generated lists, the properties box. Nothing can be typed by accident.                                               | Click the 📖 book icon at the top right of the note, or press **Ctrl+E** (**Cmd+E** on a Mac).                                                                  |
| **Live Preview** (editing) | Where you'll edit almost all the time. It looks nearly finished, but the line your cursor is on shows its formatting (`**bold**`, `[[links]]`).                    | The ✏️ pencil icon (same button as the book), or **Ctrl/Cmd+E** again.                                                                                          |
| **Source mode**            | The note's raw text, with nothing hidden or drawn. Handy when something looks wrong and you want to see exactly what's written, or to edit the properties as text. | While editing, open the **⋯** menu at the top right of the note → **Source mode** (or the command palette, **Ctrl/Cmd+P** → "Toggle Live Preview/Source mode"). |

> [!tip] Which one to use
> - **Just checking how it looks?** Reading view.
> - **Writing or fixing text?** Live Preview.
> - **Something's odd, or a link or picture won't behave?** Peek in Source mode, then switch back.

> [!warning] Generated pages
> The overview pages, the pinned guides and the Vault Map are drawn by small bits of code (grey blocks starting with `datacorejsx` or `base`). In Reading view and Live Preview you see the finished list or table. In Source mode, or if you click into one in Live Preview, you see the code instead. That's normal: click elsewhere or switch back, and **don't edit the code**. To change what a list shows, edit the notes it lists.

## Editing text

Just type! A few things are special:

| To get…                | Write…                                                                                                                     |
| :--------------------- | :------------------------------------------------------------------------------------------------------------------------- |
| A link to another note | `[[Note name]]`, or `[[Note name\|the words shown]]`                                                                       |
| A link to a heading    | `[[Note name#Heading]]`                                                                                                    |
| A picture              | Drag it into the note (it automatically saves itself into 🖼️ Assets). Add a caption with `![[picture.webp\|The caption]]` |
| A box (tip, warning…)  | `> [!note] Title` on the first line, then `> ` before each line inside. See [[Callouts]] for all the kinds                 |
| A hidden spoiler       |  Double pipe for spoilers                                                                                      |
| A Discord channel      | `[#channel-name](https://discord.com/channels/…)` (copy the link from Discord: right-click the channel → *Copy Link*)      |

**Headings** (`## Heading`, `### Smaller heading`) make the "On this page" outline on the website, and every heading gets its own link. Use them for sections instead of bold text.

> [!warning] Renaming and moving notes
> Always rename or move notes **inside Obsidian** (right-click → *Rename*, or drag in the file list). Obsidian then fixes every link to that note. Renaming in Finder or File Explorer breaks links.

## Adding new things

The easiest way is to **copy an existing note of the same kind** (right-click → *Make a copy*), rename it, and replace the contents. 

The properties at the top (the grey box) are what put a note in the right lists and tables.

| To add… | Put the note in… | Things to fill in |
| :-- | :-- | :-- |
| A deity | Deities | Tags `covalon/deity`, Domains, Divine Font… |
| A guild | Guilds | Tags `covalon/guild`, Headquarters, Leader, Members… |
| A civilization | Civilizations | Tags `covalon/civilization`, Tagline, Covalon Status, Roleplay Channel… |
| A location | City of Covalon → its district's folder | Tags `covalon/location`, **District** (a link to the district, like `[[📍 Market District\|Market District]]`) |
| An expedition | Expeditions | Tags `covalon/expedition`, Civilization, Journey Date… |
| A campaign event | Campaign Events | Tags `covalon/event`, Date, Type |
| An adventure type | Adventure Types | Tags `covalon/adventure-type`, Order (its place in the list) |
| A guide chapter | 📄 Player's Guide or 📄 GM's Guide | Name it `Chapter 13 - Title` (the next number). It's added to the guide automatically |
| A table | the guide's Tables folder | Name it `Table 3-12 - Title`, then add `![[Table 3-12 - Title]]` where it belongs in the chapter |

New notes show up by themselves on their overview page, in the tables, in the sidebar, in search and in the previous / next links.

If you need a new type of entry, please let Izzy know.
### Drafts
If you don't want a page to show up on the site yet or on any tables/etc., add the **`_published`** property and leave its box **unticked** (a newly added one shows as `-`, which counts as unticked). Tick it when the page is ready. 

If you did this right, the note gets an orange **Draft** badge and stays off the website (and out of the lists). 

Tick the box or remove the property and push to publish when it's ready.

### Hidden properties
Properties starting with `_` never show on the website:

- `_published`: unticked (or blank, `-`) makes it a draft; ticked or removed publishes it (see above).
- `_url`: a custom address for the page, like `briarmurk`.
- `_preview`: a picture for the page's Discord link preview, like `"[[CovalonCity.webp]]"`.
- `_sidebar_group`: groups a top-level folder or page in the left sidebar. Give the folder's pinned page (or the page itself, for a top-level page with no folder) the same word as the others in its section — right now `Compendiums` or `Other` — and a divider line is drawn wherever the word changes going down the list.
- A page's or folder's own name can start with an emoji too (like 🔎 How to Search) and it'll show in the sidebar the same small way `📍` does — just leave a space after it.

## Stuff to not touch
There's a buncha fiddly bits that help manage this guide and turn it into a fully functioning site. 

- The **grey code blocks** that start with `datacorejsx` or `base`. They draw the lists and tables. Edit the notes they list instead.
- The **📍 pinned notes'** generated parts. The guides and overviews fill themselves in.
- The `.site-build` and `.obsidian` folders (you won't normally see them).
## If something goes wrong
- **GitHub Desktop says there's a conflict:** someone else changed the same note. If you don't know how to fix merge conflicts, let Izzy know.
- **You made a mistake:** in GitHub Desktop, right-click a changed file → *Discard changes* to go back to the last saved version (BEFORE you push). 
  *If you do push, don't fret. Anything already pushed can always be undone from the history, it's just a bit of a pain in the ass.*
- **The website didn't update:** check the **Actions** tab on GitHub. If the latest run has a red cross, let Izzy know.

See also: [[Vault Map]] for an overview of every note and its headings.
