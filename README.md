# trrackpy

[![CI](https://github.com/kirangadhave/trrackpy/actions/workflows/ci.yml/badge.svg)](https://github.com/kirangadhave/trrackpy/actions/workflows/ci.yml)
[![PyPI - trrack](https://img.shields.io/pypi/v/trrack?label=trrack)](https://pypi.org/project/trrack/)
[![PyPI - trrack-widget](https://img.shields.io/pypi/v/trrack-widget?label=trrack-widget)](https://pypi.org/project/trrack-widget/)

Branching, tree-based provenance tracking for Python.

`trrack` records state as a branching graph of snapshots you can navigate —
undo, redo, jump to any node, or branch off an earlier state. `trrack-widget`
wraps any [anywidget](https://anywidget.dev) with time-travel controls so a
[marimo](https://marimo.io) or Jupyter widget gains a full provenance history.

## Quick start — widget

```sh
uv add trrack-widget
```

```python
from trrack_widget import Trrackable

tt = Trrackable(counter)   # any anywidget; its synced traits are tracked
tt.view                    # wrapped widget + provenance controls, side by side
```

Every change to the target's tracked traits is committed as a node. Navigate
with `tt.undo()`, `tt.redo()`, `tt.go_to(node_id)`, and label nodes with
`tt.label("checkpoint")`.

Persist a session by passing a path — state is restored on the next
construction with the same path:

```python
tt = Trrackable(counter, persist_path="state.json")
```

## Quick start — core

```sh
uv add trrack
```

```python
from trrack import ProvenanceGraph

g = ProvenanceGraph({"count": 0}, now="t0")
g.commit({"count": 1}, now="t1")
g.commit({"count": 2}, now="t2")

g.undo()            # back to {"count": 1}
g.go_to(root_id)    # jump to any node by id

g.save("graph.json")
restored = ProvenanceGraph.load("graph.json")
```

The model is pure and deterministic: timestamps are supplied via `now`, so it
performs no I/O of its own. Persistence is pluggable through the `Store`
protocol — `JsonFileStore` is built in, and any object with `save`/`load` works.

## Packages

| Package | What |
| --- | --- |
| [`trrack`](packages/trrack) | The core branching provenance model. Pure Python, no UI dependencies. |
| [`trrack-widget`](packages/trrack-widget) | An anywidget (`Trrackable`) that adds time-travel controls to any widget. |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Agents: see [AGENTS.md](AGENTS.md).

## License

BSD-3-Clause. trrackpy is a Python sibling of
[trrackjs](https://github.com/Trrack/trrackjs), bringing the same provenance
model to the Python ecosystem.
