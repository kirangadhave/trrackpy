# <img src="docs/pages/assets/favicon.svg" alt="" width="32" height="32" align="top"> trrackpy

[![CI](https://github.com/kirangadhave/trrackpy/actions/workflows/ci.yml/badge.svg)](https://github.com/kirangadhave/trrackpy/actions/workflows/ci.yml)
[![PyPI - trrack](https://img.shields.io/pypi/v/trrack?label=trrack)](https://pypi.org/project/trrack/)
[![PyPI - trrack-widget](https://img.shields.io/pypi/v/trrack-widget?label=trrack-widget)](https://pypi.org/project/trrack-widget/)

Track the state of [anywidget](https://anywidget.dev) widgets.

Read the documentation at [kirangadhave.me/trrackpy](https://kirangadhave.me/trrackpy/).

```python
from trrack_widget import JsonFileStore, Persisted, Trrackable

Persisted(counter, store=JsonFileStore("state.json"))   # comes back as you left it
Trrackable(counter)                                      # undo, redo, and branch
```

- `Persisted` saves a widget's state and restores it the next time it loads.
- `Trrackable` records every change as a history you can navigate.
- A store decides where the state lives: a file, a database, the URL. Write
  your own with two methods.

## Packages

| Package | What | Docs |
| --- | --- | --- |
| [`trrack-widget`](https://pypi.org/project/trrack-widget/) | `Persisted` and `Trrackable`, the two widget wrappers. | [packages/trrack-widget](packages/trrack-widget/README.md) |
| [`trrack`](https://pypi.org/project/trrack/) | The branching history model and the stores. Pure Python, no UI dependencies. | [packages/trrack](packages/trrack/README.md) |

## Examples

Runnable marimo notebooks are in [examples](examples/README.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, the dev loop, and releases.

## License

BSD-3-Clause. trrackpy is the Python sibling of
[trrackjs](https://github.com/Trrack/trrackjs).
