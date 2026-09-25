# Site build

These files turn this Obsidian vault into the Covalon website: plain HTML pages, no site generator.

The pages use the same structure and class names Obsidian uses in reading view, so the vault's own CSS
snippets (the ones switched on in Settings → Appearance → CSS snippets) style the site directly. Change
a snippet and the site follows at the next build. Callout colours and icons come from Callout Manager.

- `build.py`: builds the site. It expands every `![[embed]]` (the 📍 overview pages become one long page),
  turns the Bases and Datacore views into tables and entries, gives callouts Obsidian's markup, shows each
  page's properties in a panel, adds previous / next chapter navigation, and marks pages up for search.
- `assets/base.css`: stands in for Obsidian's built-in default theme (its colours, fonts and spacing), so the
  snippets have the same starting point as in Obsidian. Restyle things in the vault snippets, not here.
- `assets/site.css`, `assets/site.js`, `assets/search.js`: the frame around the notes (sidebar with the file
  tree, search box and light/dark switch; table of contents; filterable tables; the Advanced Search page).
- `requirements.txt`: the Python packages the build needs.
- `build-local.sh`: builds the site and previews it on your computer.

## Building locally

From the vault folder:

```sh
bash .site-build/build-local.sh
```

Then open http://localhost:3000. Run it again after changing notes or snippets. It needs Python 3.9 or
newer; on the first run it installs what it needs into `~/.covalon-site` (outside the vault), including
Pagefind for the search index and the Lucide icons for callouts.

## Publishing

`.github/workflows/publish.yml` (in the vault root) builds the site on GitHub and publishes it to GitHub
Pages every time the vault is pushed to `main`. In the repository's settings on GitHub, set
Pages → Source to "GitHub Actions".

## Images and Git LFS

The vault's pictures live in `🖼️ Assets` and are stored with Git LFS (see `.gitattributes` in the vault root),
so the repository stays small. On each computer that commits to the vault, run `git lfs install` once
(install Git LFS first if needed, e.g. `brew install git-lfs`). The publish workflow fetches the pictures itself.

## Pictures and caching

- Pictures are copied into the site at most 1800 pixels wide and re-compressed (`PICTURE_MAX_WIDTH` and
  `PICTURE_QUALITY` in `build.py`), so pages don't download the multi-megabyte originals. The vault's own files
  aren't changed. Animated pictures are copied as they are. The smaller copies are cached (in
  `~/.covalon-site/cache` locally, and between runs of the publish workflow), so only new or changed pictures
  take time.
- All the styles go into one file, `assets/style.css`. Its link, and the links to `site.js` and `search.js`,
  carry a stamp of the file's contents (`style.css?v=…`), so browsers pick up a new version as soon as it's
  published.

