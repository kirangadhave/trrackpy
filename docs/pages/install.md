# Install

=== "uv"

    ```sh
    uv add trrack-widget
    ```

=== "pip"

    ```sh
    pip install trrack-widget
    ```

This also installs `trrack`, the core package.

## Requirements

- Python 3.10 or later.
- The widget you wrap must be an [anywidget](https://anywidget.dev).
- marimo 0.23.14 or later, or Jupyter with anywidget 0.11 or later. Both
  wrappers show your widget inside a widget of their own, and older versions
  cannot do that.

## The core package alone

`trrack` has the history model and the stores, with no UI dependencies. Install
it alone to track the history of any Python state. See
[History without widgets](core.md).

=== "uv"

    ```sh
    uv add trrack
    ```

=== "pip"

    ```sh
    pip install trrack
    ```

Next, follow the [Quickstart](quickstart.md).
