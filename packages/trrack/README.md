# trrack

[![PyPI](https://img.shields.io/pypi/v/trrack?label=PyPI)](https://pypi.org/project/trrack/)

Branching, tree-based provenance tracking for Python. A pure model with **no UI
dependencies**: a `ProvenanceGraph` of full-state snapshots you can navigate,
branch, label, and persist.

Part of the [trrackpy](https://github.com/kirangadhave/trrackpy) monorepo; the
[`trrack-widget`](https://pypi.org/project/trrack-widget/) package is one
consumer of this core.

## Install

```sh
uv add trrack          # or: pip install trrack
```

## Concepts

- Every state you record is stored as a **full snapshot** in a `Node`. Nodes
  form a tree: committing from an earlier node creates a **branch** rather than
  discarding the later history.
- The model is **deterministic and I/O-free**. It never reads the clock —
  timestamps are passed in by the caller via `now` — so behavior is fully
  reproducible and easy to test.
- Persistence is an optional, swappable seam (`Store`); the model itself holds
  no opinion about where state is saved.

## Quick start

```python
from trrack import ProvenanceGraph

g = ProvenanceGraph({"count": 0}, now="t0")
g.commit({"count": 1}, now="t1")
g.commit({"count": 2}, now="t2")

g.undo()                 # back to {"count": 1}
g.redo()                 # forward to {"count": 2}

# Branch: go back, then commit a different state off the earlier node.
g.go_to(g.root.id)
g.commit({"count": 99}, now="t3")   # new branch from the root

g.current.state          # {"count": 99}
g.is_at_root, g.is_at_latest
```

Commits are auto-labeled from what changed; pass `label=` to name them, or
relabel later with `g.relabel("checkpoint")`.

## Persistence

Round-trip the whole graph to a JSON file:

```python
g.save("graph.json")
restored = ProvenanceGraph.load("graph.json")   # None if the file is absent
```

`save`/`load` use atomic writes (write-to-temp, then `os.replace`) so a crash
mid-write can never leave a half-written file.

For anything other than a local file, use the `Store` seam — any object with
`save(dict) -> None` and `load() -> dict | None` qualifies (a database, browser
storage, a remote service), with no registry or plugin machinery. `JsonFileStore`
is the built-in implementation:

```python
from trrack import JsonFileStore

store = JsonFileStore("graph.json")
store.save(g.to_dict())
data = store.load()                  # None if nothing saved yet
```

## API

| | |
| --- | --- |
| `ProvenanceGraph(root_state, *, now, root_id=None)` | Create a graph with a single root node. |
| `.commit(state, *, now, label=None, node_id=None)` | Append `state` as a child of the current node and move there. |
| `.undo()` / `.redo()` | Move to the parent / a child of the current node. |
| `.go_to(node_id)` | Jump to any node by id. |
| `.relabel(text, node_id=None)` | Rename a node (defaults to current). |
| `.current` / `.root` | The current / root `Node`. |
| `.is_at_root` / `.is_at_latest` | Navigation guards (nothing to undo / redo). |
| `.to_dict()` / `ProvenanceGraph.from_dict(data)` | Serialize / deserialize. |
| `.save(path)` / `ProvenanceGraph.load(path)` | JSON file persistence. |

A `Node` exposes `id`, `parent`, `children`, `created_at`, `label`, and `state`.

## License

BSD-3-Clause.
