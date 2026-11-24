# <img src="https://raw.githubusercontent.com/kirangadhave/trrackpy/main/docs/pages/assets/favicon.svg" alt="" width="32" height="32" align="top"> trrack

[![PyPI](https://img.shields.io/pypi/v/trrack?label=PyPI)](https://pypi.org/project/trrack/)

Branching history for Python state. `ProvenanceGraph` keeps every state you
record as a node in a tree. You can undo, redo, jump to any node, and branch
off an earlier one.

`trrack` is pure Python and has no UI dependencies. For widgets in notebooks,
see [`trrack-widget`](https://pypi.org/project/trrack-widget/).

## Install

```sh
uv add trrack          # or: pip install trrack
```

## Use

```python
from trrack import ProvenanceGraph

g = ProvenanceGraph({"count": 0}, now="t0")
g.commit({"count": 1}, now="t1")

g.undo()                 # back to {"count": 0}
g.current.state          # {"count": 0}
```

## Docs

Read the guide and the API reference at
[kirangadhave.me/trrackpy/core](https://kirangadhave.me/trrackpy/core/).

## License

BSD-3-Clause. Part of the
[trrackpy](https://github.com/kirangadhave/trrackpy) monorepo.
