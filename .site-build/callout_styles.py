#!/usr/bin/env python3
"""Turn the vault's Callout Manager settings into Quartz SCSS.

    python3 callout_styles.py <vault> >> quartz/styles/custom.scss

Reads <vault>/.obsidian/plugins/callout-manager/data.json and writes one rule per callout type:
- colour -> the site's --color / --border / --bg (light and dark colours map to the site's themes)
- icon   -> a Lucide icon, used as the callout's --callout-icon mask

Icons are read from node_modules/lucide-static/icons if present (npm i lucide-static),
otherwise downloaded from unpkg. A missing icon is reported and skipped.
Settings with other conditions (a specific Obsidian theme) and "custom styles" are Obsidian-only
and are skipped.
"""
import json, pathlib, sys, urllib.parse, urllib.request

VAULT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent.parent)
DATA = VAULT / ".obsidian/plugins/callout-manager/data.json"
LOCAL_ICONS = pathlib.Path("node_modules/lucide-static/icons")
UNPKG = "https://unpkg.com/lucide-static@latest/icons/{}.svg"


def warn(msg):
    print(f"callout_styles: {msg}", file=sys.stderr)


def icon_svg(icon):
    name = icon.removeprefix("lucide-")
    local = LOCAL_ICONS / f"{name}.svg"
    if local.exists():
        return local.read_text()
    try:
        with urllib.request.urlopen(UNPKG.format(name), timeout=20) as r:
            return r.read().decode()
    except Exception as e:
        warn(f"icon '{icon}' not found ({e}); skipped")
        return None


def colour_vars(rgb):
    rgb = rgb.strip()
    return (f"--color: rgb({rgb}); --border: rgba({rgb}, 0.25); --bg: rgba({rgb}, 0.1);")


def main():
    if not DATA.exists():
        warn(f"{DATA} not found; no callout styles generated")
        return
    settings = json.loads(DATA.read_text()).get("callouts", {}).get("settings", {})
    out = ["", "// ---- Generated from Callout Manager by callout_styles.py; do not edit ----"]
    for cid, entries in sorted(settings.items()):
        sel = f'.callout[data-callout="{cid}"]'
        base, light, dark = [], None, None
        for e in entries:
            cond, ch = e.get("condition"), e.get("changes", {})
            scheme = cond.get("colorScheme") if isinstance(cond, dict) else None
            if cond and not scheme:
                warn(f"'{cid}': condition {cond} is Obsidian-only; skipped")
                continue
            if ch.get("customStyles"):
                warn(f"'{cid}': custom styles are Obsidian-only; skipped")
            if ch.get("color"):
                if scheme == "light":
                    light = ch["color"]
                elif scheme == "dark":
                    dark = ch["color"]
                else:
                    base.append(colour_vars(ch["color"]))
            if ch.get("icon"):
                svg = icon_svg(ch["icon"])
                if svg:
                    svg = " ".join(svg.split())
                    base.append(f"--callout-icon: url(\"data:image/svg+xml,{urllib.parse.quote(svg)}\");")
        if base:
            out.append(f"{sel} {{ {' '.join(base)} }}")
        if light:
            out.append(f':root[saved-theme="light"] {sel} {{ {colour_vars(light)} }}')
        if dark:
            out.append(f':root[saved-theme="dark"] {sel} {{ {colour_vars(dark)} }}')
    print("\n".join(out))


if __name__ == "__main__":
    main()
