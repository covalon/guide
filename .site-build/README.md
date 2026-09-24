# Site build

These files turn this Obsidian vault into a website with [Quartz](https://quartz.jzhao.xyz/).
The folder starts with a dot so Obsidian doesn't show it as notes.

- `build_site.py`: converts the vault into Quartz content. It expands every embed on the 📍 overview pages
  into one long page, turns the Bases and Datacore views into plain tables and headings, shows each note's
  properties at the top of its page, turns image alt text into captions, and adds previous / next chapter
  navigation to the chapter pages.
- `quartz.config.ts`, `quartz.layout.ts`, `custom.scss`: the Quartz settings, page layout and styling.
  The site address is set in `quartz.config.ts` (`baseUrl`).

## Building locally

```sh
git clone --depth 1 --branch v4.5.2 https://github.com/jackyzha0/quartz.git /tmp/quartz
cd /tmp/quartz && npm ci
cp <vault>/.site-build/quartz.config.ts <vault>/.site-build/quartz.layout.ts .
cp <vault>/.site-build/custom.scss quartz/styles/custom.scss
python3 <vault>/.site-build/build_site.py <vault> content     # needs: pip install pyyaml
npx quartz build --serve                                      # preview at http://localhost:8080
```

## Publishing

Not set up yet. The plan is a separate GitHub repository for the vault (e.g. `covalon/obs-covalon-guide`)
with a GitHub Actions workflow that runs the steps above and deploys `public/` to GitHub Pages.
