#!/usr/bin/env bash
# Build the Covalon site from this vault and preview it at http://localhost:3000
#   bash .site-build/build-local.sh          (run from the vault folder; Ctrl+C stops the preview)
# Needs Python 3.9+. Everything else (the Python packages, the search tool, the callout icons) is set up
# on the first run in ~/.covalon-site, outside the vault.
set -euo pipefail

SITE="$(cd "$(dirname "$0")" && pwd)"     # .site-build
VAULT="$(dirname "$SITE")"
HOME_DIR="${COVALON_SITE_HOME:-$HOME/.covalon-site}"
OUT="$HOME_DIR/public"
PY="$HOME_DIR/.venv/bin/python3"

if [ ! -x "$PY" ]; then
  echo "▶ Setting up (first run only)…"
  mkdir -p "$HOME_DIR"
  python3 -m venv "$HOME_DIR/.venv"
fi
"$PY" -m pip install --quiet --disable-pip-version-check -r "$SITE/requirements.txt"

echo "▶ Building the site…"
COVALON_CACHE="$HOME_DIR/cache" "$PY" "$SITE/build.py" "$VAULT" "$OUT"
echo "▶ Taking the tables' preview pictures…"
"$PY" -m playwright install chromium >/dev/null
COVALON_CACHE="$HOME_DIR/cache" "$PY" "$SITE/previews.py" "$OUT"
echo "▶ Building the search index…"
"$PY" -m pagefind --site "$OUT" --silent

echo "▶ Preview at http://localhost:3000 (Ctrl+C to stop)"
"$PY" -m http.server 3000 --directory "$OUT" --bind 127.0.0.1
