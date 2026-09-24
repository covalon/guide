# Site build

These files turn this Obsidian vault into a website with [Quartz](https://quartz.jzhao.xyz/).
The folder starts with a dot so Obsidian doesn't show it as notes.

- `build_site.py`: converts the vault into Quartz content. It expands every embed on the 📍 overview pages
  into one long page, turns the Bases and Datacore views into plain tables and headings, shows each note's
  properties at the top of its page, turns image alt text into captions, and adds previous / next chapter
  navigation to the chapter pages.
- `callout_styles.py`: turns the Callout Manager plugin's settings (callout colours, icons, new callout types)
  into site CSS, so callouts on the site match the vault.
- `components/`: two small Quartz components. `PagefindSearch.tsx` is the Advanced Search page (Pagefind, with
  filters for page type and properties such as domains, soul seed and district; `build_site.py` marks each page's
  properties as filters). `FilterableTables.tsx` adds a filter box, drop-downs and sortable headers to the tables
  from the vault's Bases.
- `quartz.config.ts`, `quartz.layout.ts`, `custom.scss`: the Quartz settings, page layout and styling.
  The site address is set in `quartz.config.ts` (`baseUrl`).

## Building locally

Run `bash .site-build/build-local.sh` from the vault folder. It downloads Quartz once (into `~/.covalon-quartz`),
copies in the settings, components and styles from this folder, converts the vault, builds the site and the search
index, and serves it at http://localhost:3000. Run it again after editing notes to see the changes.

Needs git, Node.js 22 or newer, and Python 3 with PyYAML (`pip3 install pyyaml`).

## Publishing

Not set up yet. The plan is a separate GitHub repository for the vault (e.g. `covalon/obs-covalon-guide`)
with a GitHub Actions workflow that runs the steps above and deploys `public/` to GitHub Pages.
