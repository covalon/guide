#!/usr/bin/env bash
# Build the Covalon site from this vault and preview it at http://localhost:3000
# Usage (from anywhere):  bash "<vault>/.site-build/build-local.sh"
# Needs: git, Node.js 22+, Python 3 with PyYAML (pip3 install pyyaml).
# Quartz is downloaded once into ~/.covalon-quartz and reused on later runs.
set -euo pipefail

SITE="$(cd "$(dirname "$0")" && pwd)"      # .site-build
VAULT="$(dirname "$SITE")"
Q="${QUARTZ_DIR:-$HOME/.covalon-quartz}"

if [ ! -d "$Q" ]; then
  echo "▶ Downloading Quartz (first run only)…"
  git clone --depth 1 --branch v4.5.2 https://github.com/jackyzha0/quartz.git "$Q"
  (cd "$Q" && npm ci && npm i --no-save lucide-static)
fi

cd "$Q"
echo "▶ Copying site settings, components and styles…"
cp "$SITE/quartz.config.ts" "$SITE/quartz.layout.ts" .
cp "$SITE/components/"*.tsx quartz/components/
cp "$SITE/static/"* quartz/static/
cp "$SITE/custom.scss" quartz/styles/custom.scss
python3 "$SITE/callout_styles.py" "$VAULT" >> quartz/styles/custom.scss

echo "▶ Converting the vault…"
python3 "$SITE/build_site.py" "$VAULT" content

echo "▶ Building the site…"
npx quartz build
echo "▶ Building the search index…"
npx -y pagefind --site public

echo "▶ Serving at http://localhost:3000 (Ctrl+C to stop)"
npx -y serve public -l 3000
