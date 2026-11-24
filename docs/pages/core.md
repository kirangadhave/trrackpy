# History without widgets

The `trrack` package keeps a branching history of any dict of values. It uses
only the Python standard library.

To install it, see [Install](install.md#the-core-package-alone). For the ideas
behind the history, see [How the history works](concepts.md).

## Record states

Create a `ProvenanceGraph` with the first state. Call `commit` to record each
next state:

```python
from trrack import ProvenanceGraph

g = ProvenanceGraph({"count": 0}, now="t0")
g.commit({"count": 1}, now="t1")
g.commit({"count": 2}, now="t2")

g.current.state          # {"count": 2}
g.current.label          # "count: 1 → 2"
```

`commit` returns the new node and makes it the current node. Pass `label` to
name the node yourself:

```python
g.commit({"count": 3}, now="t3", label="manual bump")
```

## Move through the history

```python
g.undo()                 # to the parent, returns the node
g.redo()                 # to the newest child, returns the node
g.go_to(node_id)         # to any node, returns the node
```

`undo` returns `None` at the root, and `redo` returns `None` at a node with
no children. `go_to` raises `KeyError` for an id that is not in the graph.

Read the position with these properties:

```python
g.current                # the current node
g.root                   # the first node
g.is_at_root             # True when there is nothing to undo
g.is_at_latest           # True when there is nothing to redo
```

A node has `id`, `parent`, `children`, `created_at`, `label`, and `state`.

## Branch

Go back, then commit a different state. The graph adds a new branch and keeps
the old one:

```python
g.go_to(g.root.id)
g.commit({"count": 99}, now="t4")

g.root.children          # two ids, one for each branch
```

## Rename a node

```python
g.relabel("start", g.root.id)   # a node by id
g.relabel("big jump")           # the current node
```

## Timestamps

You pass each timestamp as `now`. The graph never reads the clock. Any string
works, such as an ISO time:

```python
from datetime import datetime, timezone

g.commit({"count": 4}, now=datetime.now(timezone.utc).isoformat())
```

## Convert to plain data

`to_dict` gives plain data that `json` can write. `from_dict` rebuilds the
graph:

```python
data = g.to_dict()
g2 = ProvenanceGraph.from_dict(data)

g2.current.state == g.current.state   # True
```

The rebuilt graph keeps the current node.

## Save to a file

`JsonFileStore` keeps a dict in one JSON file:

```python
from trrack import JsonFileStore

store = JsonFileStore("history.json")
store.save(g.to_dict())

g3 = ProvenanceGraph.from_dict(store.load())
```

`load` returns `None` when the file does not exist. To keep the history
somewhere else, see [Stores](stores.md).

See the [API reference](api/core.md) for every class and function.
