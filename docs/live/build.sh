#!/usr/bin/env bash
# Builds the live notebooks that the docs embed. Run it from any directory,
# then run `zensical build` or `zensical serve`.
#
# Each notebook runs in the browser on Pyodide. It installs the wheels of this
# repo, so the live examples always match the checked-out source.
set -euo pipefail

cd "$(dirname "$0")/../.."

widget=packages/trrack-widget
wheels=docs/live/public
out=docs/pages/live

# The widget wheel ships the compiled frontend. Bundle it each time, so the
# wheel never holds a stale bundle.
(cd "$widget" && pnpm install && pnpm run build)

# marimo copies a `public/` folder that sits next to a notebook into its export.
# The notebooks read `wheels.txt` for the file names, so no version number
# appears outside the package metadata.
rm -rf "$wheels" "$out"
mkdir -p "$wheels"
uv build --package trrack --wheel --out-dir "$wheels"
uv build --package trrack-widget --wheel --out-dir "$wheels"
(cd "$wheels" && ls ./*.whl | sed 's|^\./||' > wheels.txt)

for notebook in trrackable persisted; do
  uv run --only-group docs marimo export html-wasm \
    "docs/live/$notebook.py" -o "$out/$notebook" --mode run
done

# marimo adds a `CLAUDE.md` for coding agents. Zensical would publish it as a page.
find "$out" -name '*.md' -delete
