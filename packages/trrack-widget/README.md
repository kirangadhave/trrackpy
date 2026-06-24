# trrack-widget

[![PyPI](https://img.shields.io/pypi/v/trrack-widget?label=PyPI)](https://pypi.org/project/trrack-widget/)

An [anywidget](https://anywidget.dev) that wraps any widget and records its
state as a branching provenance history you can navigate — undo, redo, jump to
any node, branch off an earlier state, and label checkpoints. Works in
[marimo](https://marimo.io) and Jupyter.

Built on [`trrack`](https://pypi.org/project/trrack/) (the pure provenance
core); part of the [trrackpy](https://github.com/kirangadhave/trrackpy)
monorepo.

## Install

```sh
uv add trrack-widget          # or: pip install trrack-widget
```

`trrack` is pulled in automatically.

## Quick start

Wrap any anywidget; its synced traits are tracked, and every change is committed
as a node in the history.

```python
from trrack_widget import Trrackable

tt = Trrackable(counter)   # counter is any anywidget.AnyWidget
tt.view                    # wrapped widget + provenance controls, side by side
```

Drive it from Python as well as the UI:

```python
tt.undo()
tt.redo()
tt.go_to(node_id)          # jump to any node
tt.label("before tuning")  # name the current node
```

## Display

- `tt.view` — the target and the controls side by side. Uses `marimo.hstack`
  when marimo is available, otherwise falls back to `ipywidgets.HBox`.
- `tt.widget` — just the wrapped target.
- `tt.controls` — just the provenance control UI.

## Constructor options

```python
Trrackable(
    target,                 # the widget to track
    traits=None,            # trait names to track; defaults to the target's
                            # public synced traits
    *,
    debounce_ms=0,          # coalesce rapid trait changes into one commit
    persist_path=None,      # convenience: persist to this JSON file
    store=None,             # any trrack.Store; takes precedence over persist_path
)
```

## Persistence

Pass `persist_path` to make a session durable. State is restored on the next
construction with the same path (the file is authoritative), and written after
every mutation, coalesced and atomic:

```python
tt = Trrackable(counter, persist_path="state.json")
# ... interact ...
tt.flush_persist()         # force any pending write immediately
```

For a non-file backend, pass any `trrack.Store`:

```python
from trrack import JsonFileStore

tt = Trrackable(counter, store=JsonFileStore("state.json"))
```

## Frontend

The control UI is a React + TypeScript component bundled to
`src/trrack_widget/static/controls.js`. Installed wheels ship the prebuilt
bundle, so end users never need Node. See the
[monorepo CONTRIBUTING guide](https://github.com/kirangadhave/trrackpy/blob/main/CONTRIBUTING.md)
for the frontend dev loop.

## License

BSD-3-Clause.
