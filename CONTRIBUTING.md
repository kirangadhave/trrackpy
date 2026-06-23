# Contributing to trrackpy

Thanks for contributing. This guide gets you from a fresh clone to a green pull
request.

## Layout

trrackpy is a [uv](https://docs.astral.sh/uv/) workspace with two packages:

- `packages/trrack` — the **core**: a pure-Python branching provenance model
  (`ProvenanceGraph`) plus a `Store` persistence seam. Zero UI dependencies.
- `packages/trrack-widget` — the **widget**: an [anywidget](https://anywidget.dev)
  that wraps any widget with time-travel controls (`Trrackable`). It depends on
  `trrack` through the local workspace source, never the published package.

The split is deliberate: the core can be used on its own to track the history of
anything, and the widget is just one consumer of it.

## Setup

The frontend bundle (`src/trrack_widget/static/controls.js`) is a gitignored
build artifact. Build it **before** `uv sync` so the editable install can ship
it:

```sh
cd packages/trrack-widget
pnpm install
pnpm run build
cd ../..
uv sync
```

## Frontend dev loop

The controls UI is a React + TypeScript component in
`packages/trrack-widget/js/controls.tsx`, bundled by esbuild. Rebuild on every
save with:

```sh
cd packages/trrack-widget
pnpm run dev
```

With `ANYWIDGET_HMR=1 uv run marimo edit trrack-widget-demo.py` the rebuilt
bundle hot-swaps into active cells without a kernel restart.

## Checks before a PR

Run the full gate, or let pre-commit do it for you:

```sh
uv run pytest
uv run ruff check
uv run ruff format --check
uv run ty check
cd packages/trrack-widget && pnpm run lint && pnpm run typecheck && cd ../..
```

```sh
uvx pre-commit run --all-files
```

## Conventions

- [Conventional commits](https://www.conventionalcommits.org/): `feat:`, `fix:`,
  `chore:`, `docs:`, `refactor:`, `test:`.
- Python is linted with ruff (`select = ["ALL"]`) and type-checked with `ty`;
  both must stay clean. `from __future__ import annotations` is required at the
  top of every module.
- New files fall under the repository's BSD-3-Clause license.

## Where to add things

- A change to the model or its algorithms goes in `packages/trrack`.
- UI and widget wiring goes in `packages/trrack-widget`.
- A new persistence backend implements the `trrack.Store` protocol
  (`save(dict) -> None`, `load() -> dict | None`) — no registry or plugin
  machinery to touch.
