# trrack

[![PyPI](https://img.shields.io/pypi/v/trrack?label=PyPI)](https://pypi.org/project/trrack/)

Branching history for Python state. `ProvenanceGraph` keeps every state you
record as a node in a tree, so you can undo, redo, jump to any node, and branch
off an earlier one.

Pure Python, with no UI dependencies. For widgets in notebooks, see
[`trrack-widget`](https://pypi.org/project/trrack-widget/).

## Install

```sh
uv add trrack          # or: pip install trrack
```

## Use

```python
from trrack import ProvenanceGraph

g = ProvenanceGraph({"count": 0}, now="t0")
g.commit({"count": 1}, now="t1")
g.commit({"count": 2}, now="t2")

g.undo()                 # back to {"count": 1}
g.redo()                 # forward to {"count": 2}

# Go back, then commit a different state. This starts a new branch.
g.go_to(g.root.id)
g.commit({"count": 99}, now="t3")

g.current.state          # {"count": 99}
```

The graph never reads the clock. You pass each timestamp as `now`, so the same
calls always build the same graph.

`g.to_dict()` gives a JSON-compatible dict, and
`ProvenanceGraph.from_dict(data)` rebuilds the graph.

## Docs

The API reference and the guide to stores are at
[kirangadhave.github.io/trrackpy](https://kirangadhave.github.io/trrackpy/).

## License

BSD-3-Clause. Part of the
[trrackpy](https://github.com/kirangadhave/trrackpy) monorepo.
