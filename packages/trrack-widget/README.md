# <img src="https://raw.githubusercontent.com/kirangadhave/trrackpy/main/docs/pages/assets/favicon.svg" alt="" width="32" height="32" align="top"> trrack-widget

[![PyPI](https://img.shields.io/pypi/v/trrack-widget?label=PyPI)](https://pypi.org/project/trrack-widget/)

Track the state of [anywidget](https://anywidget.dev) widgets.

- `Persisted` saves a widget's state and restores it the next time it loads.
- `Trrackable` records every change as a history you can undo, redo, and
  branch.

## Install

```sh
uv add trrack-widget          # or: pip install trrack-widget
```

## Use

```python
from trrack_widget import JsonFileStore, Persisted, Trrackable

Persisted(counter, store=JsonFileStore("state.json"))   # comes back as you left it
Trrackable(counter)                                      # undo, redo, and branch
```

## Docs

Read the guides, the examples, and the API reference at
[kirangadhave.me/trrackpy](https://kirangadhave.me/trrackpy/).

## Requirements

- The wrapped widget must be an anywidget.
- marimo 0.23.14 or later, or Jupyter with anywidget 0.11 or later.

## License

BSD-3-Clause. Part of the
[trrackpy](https://github.com/kirangadhave/trrackpy) monorepo.
