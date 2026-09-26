"""Pictures of the tables for the link previews (Discord cards and other apps' previews).

Run after build.py, on the built site:   python .site-build/previews.py public
The build lists the tables in public/_previews.json (site address of each picture -> the table's HTML).
Each one is photographed in light mode with the site's own styles by a headless Chromium (Playwright;
install it once with:  python -m playwright install chromium). Pictures are kept in the build cache
(COVALON_CACHE, ~/.cache/covalon-site) by name, and the name comes from the table's contents and the
site's styles, so only new or changed tables are photographed again.
"""
import json
import os
import pathlib
import shutil
import sys

OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "public").resolve()
CACHE = pathlib.Path(os.environ.get("COVALON_CACHE", pathlib.Path.home() / ".cache" / "covalon-site")) / "previews"
WIDTH = 960        # the width the tables are laid out in
MAX_HEIGHT = 900   # taller tables are cut off here, fading out
THUMB_SIZE = 2400  # the square copy for Discord card thumbnails, kept at full size (tables are photographed at 2x)

PAGE = """<!doctype html>
<html class="theme-light"><head><meta charset="utf-8"><link rel="stylesheet" href="{css}">
<style>
  html, body {{ margin: 0; overflow: hidden; }}
  .shot {{ display: inline-block; padding: 20px; max-width: {width}px; box-sizing: border-box; }}
  .shot table {{ margin: 0; }}
  .shot {{ position: relative; max-height: {max_height}px; overflow: hidden; }}
  .shot.is-cut::after {{ content: ""; position: absolute; inset: auto 0 0 0; height: 140px;
    background: linear-gradient(transparent, var(--background-primary)); }}
  .covalon-shot-more td {{ text-align: center; font-style: italic; color: var(--text-muted); }}
</style></head>
<body class="theme-light"><div class="markdown-preview-view markdown-rendered"><div class="shot">{table}</div></div></body></html>"""


def main():
    jobs_file = OUT / "_previews.json"
    if not jobs_file.exists():
        print("previews: no _previews.json (run build.py first)")
        return
    jobs = json.loads(jobs_file.read_text(encoding="utf-8"))
    CACHE.mkdir(parents=True, exist_ok=True)
    todo = {url: table for url, table in jobs.items() if not (CACHE / pathlib.Path(url).name).exists()}
    if todo:
        from playwright.sync_api import sync_playwright
        css = (OUT / "assets" / "style.css").as_uri()
        tmp = OUT / "_preview-shot.html"
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": WIDTH + 40, "height": 800}, device_scale_factor=2)
            for url, table in todo.items():
                tmp.write_text(PAGE.format(css=css, table=table, width=WIDTH + 40, max_height=MAX_HEIGHT), encoding="utf-8")
                page.goto(tmp.as_uri())
                page.wait_for_load_state("networkidle")
                page.evaluate("() => { const s = document.querySelector('.shot'); s.classList.toggle('is-cut', s.scrollHeight > s.clientHeight + 1); }")
                page.locator(".shot").screenshot(path=str(CACHE / pathlib.Path(url).name), type="jpeg", quality=85)
            browser.close()
        tmp.unlink()
    from PIL import Image
    for url in jobs:
        dest = OUT / url
        dest.parent.mkdir(parents=True, exist_ok=True)
        shot = CACHE / pathlib.Path(url).name
        shutil.copy(shot, dest)
        # the square copy for Discord's thumbnail: the whole table centred on a see-through square
        thumb = shot.with_name(shot.stem + "-thumb.webp")
        if not thumb.exists():
            with Image.open(shot) as im:
                im = im.convert("RGBA")
                side = max(im.size)
                canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
                canvas.paste(im, ((side - im.width) // 2, (side - im.height) // 2))
                if side > THUMB_SIZE:
                    canvas = canvas.resize((THUMB_SIZE, THUMB_SIZE), Image.LANCZOS)
                canvas.save(thumb, "WEBP", quality=85, method=4)
        shutil.copy(thumb, dest.with_name(thumb.name))
    jobs_file.unlink()
    print(f"previews: {len(jobs)} table pictures ({len(todo)} new)")


if __name__ == "__main__":
    main()
