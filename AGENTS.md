# AGENTS.md

Guidance for coding agents working in trrackpy.

## Orientation

trrackpy saves and tracks the state of notebook widgets. It is a
[uv](https://docs.astral.sh/uv/) workspace of two packages:

- `packages/trrack`: the core. A branching history model and the stores. Pure
  Python, no UI dependencies.
- `packages/trrack-widget`: two [anywidget](https://anywidget.dev) wrappers.
  `Persisted` saves a widget's state. `Trrackable` records its history with
  undo and redo. Uses `trrack` from the local workspace source.

`examples` has runnable marimo notebooks for both wrappers.

## Build / test commands

```sh
cd packages/trrack-widget && pnpm install && pnpm run build && cd ../..  # bundle first
uv sync                                                                   # then install
uv run pytest                                                             # both suites
uv run ruff check && uv run ruff format --check                          # lint + format
uv run ty check                                                           # type check
cd packages/trrack-widget && pnpm run lint && pnpm run typecheck && cd ../..  # JS gate
```

## Invariants: do not break

- `trrack` stays free of UI dependencies. Nothing in `packages/trrack` imports
  anywidget, traitlets, or marimo.
- `ProvenanceGraph` stays deterministic and I/O-free. The caller passes each
  timestamp as `now`. The model never reads the clock and never touches files.
- Saving goes through the `trrack.Store` protocol: `save` and `load`. Add a
  store by writing those two methods. Do not add a registry or plugin system.
- Saved payloads are tagged `{"type": "graph" | "state", "value": ...}`. A
  payload with no `type` is a graph.
- Each node stores a full snapshot of the state. Do not change this to diffs
  without a decision from the maintainer.
- The wrapped widget must be an anywidget. Both wrappers show it through
  anywidget composition (`host.getWidget`), not through host layout code.

## Code-nav pointers

- `packages/trrack/src/trrack/graph.py`: `ProvenanceGraph` and `Node`.
- `packages/trrack/src/trrack/persist.py`: the `Store` protocol,
  `JsonFileStore`, `to_state`, `from_state`, and the payload tags.
- `packages/trrack-widget/src/trrack_widget/persisted.py`: `Persisted`.
- `packages/trrack-widget/src/trrack_widget/widget.py`: `Trrackable`.
- `packages/trrack-widget/src/trrack_widget/_base.py`: what both wrappers
  share: the `target` and `error` traits, and the link to the target.
- `packages/trrack-widget/src/trrack_widget/_tracked.py`: `TrackedValues`,
  which reads, sets, and observes the tracked traits of the target.
- `packages/trrack-widget/src/trrack_widget/_persist.py`: `Debouncer` and
  `CoalescedWriter`, the batched store writes.
- `packages/trrack-widget/js/compose.ts`: shows the wrapped widget and the
  error line. `controls.tsx` (history controls, Preact) and `persisted.ts`
  both use it.
- `examples`: marimo notebooks, in `persisted` and `trrackable`.
- `docs/pages` and `mkdocs.yml`: the docs site, built with Zensical. The API
  reference pages come from the docstrings, so a public docstring is public
  documentation. `docs/agents` is not part of the site.

## Conventions

- ruff, `ty`, and oxlint must stay green.
- [Conventional commits](https://www.conventionalcommits.org/).
- Do not commit `src/trrack_widget/static/`. It is gitignored build output.

## Agent skills

### Issue tracker

Issues and specs live in GitHub Issues for `kirangadhave/trrackpy`. See `docs/agents/issue-tracker.md`.

### Triage labels

The five default triage labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `CONTEXT.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
