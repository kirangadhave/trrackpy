# Install

```sh
uv add trrack-widget
```

Or with pip:

```sh
pip install trrack-widget
```

This also installs `trrack`, the core package.

## Requirements

- Python 3.10 or later.
- The widget you wrap must be an [anywidget](https://anywidget.dev).
- marimo 0.23.14 or later, or Jupyter with anywidget 0.11 or later. Both
  wrappers show your widget inside their own, and older versions cannot do
  that.

## The core package alone

`trrack` has the history model and the stores, with no UI dependencies. Install
it alone to track the history of any Python state:

```sh
uv add trrack
```

See the [core API reference](api/core.md).
