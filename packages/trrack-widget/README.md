# trrack-widget

[![PyPI](https://img.shields.io/pypi/v/trrack-widget?label=PyPI)](https://pypi.org/project/trrack-widget/)

Save and track the state of [anywidget](https://anywidget.dev) widgets in
[marimo](https://marimo.io) and Jupyter.

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

The store decides where the state lives. `JsonFileStore` uses a file. Write
your own with two methods, `save` and `load`, to use a database or the URL.

## Docs

The guide, the examples, and the API reference are at
[kirangadhave.github.io/trrackpy](https://kirangadhave.github.io/trrackpy/).

## Requirements

- The wrapped widget must be an anywidget.
- marimo 0.23.14 or later, or Jupyter with anywidget 0.11 or later.

## License

BSD-3-Clause. Part of the
[trrackpy](https://github.com/kirangadhave/trrackpy) monorepo.
