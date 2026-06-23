# AGENTS.md

Guidance for coding agents working in trrackpy.

## Orientation

trrackpy tracks the history of state as a branching provenance graph and lets
you navigate it (undo, redo, jump to any node, branch off an earlier state). It
is a [uv](https://docs.astral.sh/uv/) workspace of two packages:

- `packages/trrack` — the **core** model. Pure Python, no UI dependencies.
- `packages/trrack-widget` — an [anywidget](https://anywidget.dev) (`Trrackable`)
  that wraps any widget with time-travel controls. Consumes `trrack` from the
  local workspace source.

The core is pure; the widget consumes it locally.

## Build / test commands

```sh
cd packages/trrack-widget && pnpm install && pnpm run build && cd ../..  # bundle first
uv sync                                                                   # then install
uv run pytest                                                             # both suites
uv run ruff check && uv run ruff format --check                          # lint + format
uv run ty check                                                           # type check
cd packages/trrack-widget && pnpm run lint && pnpm run typecheck && cd ../..  # JS gate
```

## Invariants — do not break

- `trrack` stays free of UI dependencies. Nothing in `packages/trrack` imports
  anywidget, traitlets, marimo, or React.
- `ProvenanceGraph` stays deterministic and I/O-free: timestamps are injected by
  the caller via `now`, never read from the clock inside the model.
- Persistence goes through the `trrack.Store` protocol. Add backends by
  implementing `save`/`load`; do not introduce a registry or plugin system.
- The node model stores **full state snapshots** per node. Diff-based nodes are a
  documented future option (see `packages/trrack/src/trrack/persist.py`), not a
  change to make casually.

## Code-nav pointers

- `packages/trrack/src/trrack/graph.py` — `ProvenanceGraph` and `Node` (the model).
- `packages/trrack/src/trrack/persist.py` — `Store` protocol, `JsonFileStore`,
  atomic JSON helpers.
- `packages/trrack-widget/src/trrack_widget/widget.py` — the `Trrackable` adapter.
- `packages/trrack-widget/js/controls.tsx` — the React controls UI.

## Conventions

- ruff, `ty`, and oxlint must stay green.
- [Conventional commits](https://www.conventionalcommits.org/).
- Do not commit the `src/trrack_widget/static/` bundle — it is a gitignored
  build artifact.
