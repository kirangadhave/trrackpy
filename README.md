# trrackpy

[![CI](https://github.com/kirangadhave/trrackpy/actions/workflows/ci.yml/badge.svg)](https://github.com/kirangadhave/trrackpy/actions/workflows/ci.yml)
[![PyPI - trrack](https://img.shields.io/pypi/v/trrack?label=trrack)](https://pypi.org/project/trrack/)
[![PyPI - trrack-widget](https://img.shields.io/pypi/v/trrack-widget?label=trrack-widget)](https://pypi.org/project/trrack-widget/)

Save and track the state of widgets in [marimo](https://marimo.io) and Jupyter.

```python
from trrack_widget import JsonFileStore, Persisted, Trrackable

Persisted(counter, store=JsonFileStore("state.json"))   # comes back as you left it
Trrackable(counter)                                      # undo, redo, and branch
```

- `Persisted` saves a widget's state and restores it the next time it loads.
- `Trrackable` records every change as a history you can navigate.
- A store decides where the state lives: a file, a database, the URL. Write
  your own with two methods.

Both work with any [anywidget](https://anywidget.dev).

## Packages

| Package | What | Docs |
| --- | --- | --- |
| [`trrack-widget`](https://pypi.org/project/trrack-widget/) | `Persisted` and `Trrackable`, the two widget wrappers. | [packages/trrack-widget](packages/trrack-widget/README.md) |
| [`trrack`](https://pypi.org/project/trrack/) | The branching history model and the stores. Pure Python, no UI dependencies. | [packages/trrack](packages/trrack/README.md) |

## Examples

Runnable notebooks are in [examples](examples/README.md).

## Contributing

This is a [uv](https://docs.astral.sh/uv/) workspace. See
[CONTRIBUTING.md](CONTRIBUTING.md) for setup, the dev loop, and the release
flow; agents, see [AGENTS.md](AGENTS.md).

## License

BSD-3-Clause. trrackpy is a Python sibling of
[trrackjs](https://github.com/Trrack/trrackjs), bringing the same provenance
model to the Python ecosystem.
